"""Actual API demo: optional live HTTP, otherwise ASGI HTTP; always real SQL/model/Neo4j.

Neo4j outage uses a separate app with explicit fault injection. No production fault switches.
"""
from phase07_common import *
import argparse, time
import httpx
from fastapi.testclient import TestClient
from backend.app.main import create_app


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base-url');args=parser.parse_args()
    app=create_app();rows=[];runs=[]
    client=httpx.Client(base_url=args.base_url,timeout=90) if args.base_url else TestClient(app)
    cases=[('normal_education',{'assessment':SYNTHETIC,'is_synthetic':True,'question':'What risk factors for type 2 diabetes are described?'},'DEGRADED'),
           ('coordination',{'question':'What diabetes symptoms include thirst?'},'COMPLETED'),
           ('unsafe_medication',{'question':'Should I increase my insulin dose?'},'BLOCKED')]
    try:
        with client:
            for name,body,expected in cases:
                start=time.perf_counter();response=client.post('/api/v1/mas/runs',json=body);elapsed=(time.perf_counter()-start)*1000
                response.raise_for_status();run=response.json()
                assert run['status']==expected,(name,run['status'])
                if name=='normal_education':
                    assert all(run['agent_results'][a]['status']=='COMPLETED' for a in ['prediction','knowledge','rl','education','safety'])
                    assert run['agent_results']['prediction']['output']['persisted_record_id'] and run['evidence']
                if name=='coordination':
                    assert run['evidence'] and run['agent_results']['rl']['output']['decision_source']=='policy'
                    assert all(e['evidence_id'] in run['response'] for e in run['evidence'])
                if name=='unsafe_medication':
                    assert not run['evidence'] and run['agent_results']['rl']['status']=='SKIPPED'
                    assert 'S01_MEDICATION_DOSING' in run['safety_decisions'][0]['rule_ids']
                assert client.get('/api/v1/mas/runs/'+run['run_id']).json()==run
                assert client.get('/api/v1/mas/runs/'+run['run_id']+'/trace').json()['agent_trace']==run['agent_trace']
                assert [d['stage'] for d in run['safety_decisions']]==['input','output']
                assert all(e['run_id']==run['run_id'] for e in run['agent_trace'])
                rows.append({'scenario':name,'run_id':run['run_id'],'status':run['status'],'passed':1,'latency_ms':elapsed,'transport':'live HTTP' if args.base_url else 'ASGI HTTP','fault':'none'})
                runs.append({'scenario':name,'run':run})
        fault_app=create_app(engine=app.state.db_engine,model_service=app.state.model_service,policy_service=app.state.policy_service,knowledge_store=UnavailableGraph())
        with TestClient(fault_app) as fault_client:
            started=time.perf_counter();response=fault_client.post('/api/v1/mas/runs',json={'question':'What diabetes symptoms include thirst?'});elapsed=(time.perf_counter()-started)*1000
            assert response.status_code==201,response.text
            run=response.json();assert run['status']=='DEGRADED' and not run['evidence']
            assert run['agent_results']['knowledge']['status']=='UNAVAILABLE'
            assert fault_client.get('/api/v1/mas/runs/'+run['run_id']).json()==run
            rows.append({'scenario':'knowledge_unavailable','run_id':run['run_id'],'status':run['status'],'passed':1,'latency_ms':elapsed,'transport':'ASGI HTTP','fault':'explicit Neo4j connection failure simulation; other services real'})
            runs.append({'scenario':'knowledge_unavailable','run':run})
    finally:
        app.state.knowledge_store.close();app.state.db_engine.dispose()
    save('e2e',[{'scenarios':len(rows),'passed':sum(r['passed'] for r in rows)}],rows,'Four executed SYNTHETIC API scenarios with persisted GET/trace readback; no frontend or agent outputs hardcoded.',datasets=['experiments/configs/phase07_scenarios.json'],config={'api':'/api/v1/mas/runs','base_url':args.base_url or 'in-process ASGI TestClient','neo4j_outage':'isolated dependency injection; no production fault endpoint'},extra={'runs':runs})

if __name__=='__main__':main()
