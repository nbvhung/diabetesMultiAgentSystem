"""Runtime 3.0 actual API demo with immutable source evidence and persisted trace."""
from phase07_common import *
import argparse,time
import httpx
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.research.api import Services
from backend.app.research.config import ResearchSettings
from backend.app.research.llm import GroqService


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base-url');args=parser.parse_args()
    app=create_app();svc=Services(app.state);app.state.research_services=svc
    client=httpx.Client(base_url=args.base_url,timeout=120) if args.base_url else TestClient(app)
    cases=[('synthetic_assessment_and_risk',{'question':'Bệnh tiểu đường týp 2 có những yếu tố nguy cơ nào?','assessment':SYNTHETIC,'is_synthetic':True},True,False),
           ('vietnamese_education',{'question':'Bệnh tiểu đường có những triệu chứng nào?'},True,False),
           ('unsafe_medication',{'question':'Tôi nên tăng liều insulin lên bao nhiêu?'},False,True),
           ('missing_evidence',{'question':'Tell me about sugar'},False,False)]
    rows=[];runs=[]
    try:
        with client:
            for name,body,requires_evidence,blocked in cases:
                start=time.perf_counter();response=client.post('/api/v2/mas/runs',json=body);elapsed=(time.perf_counter()-start)*1000;response.raise_for_status();run=response.json()
                assert run['schema_version']=='3.0'
                assert (run['status']=='BLOCKED')==blocked
                assert bool(run['evidence'])==requires_evidence
                if requires_evidence:
                    assert run['grounding']['verified'] and run['generation_mode'] in ('llm','extractive')
                    assert run['agent_results']['verifier']['status']=='COMPLETED'
                else:assert not run['evidence']
                assert client.get('/api/v2/mas/runs/'+run['run_id']).json()==run
                assert client.get('/api/v2/mas/runs/'+run['run_id']+'/trace').json()['agent_trace']==run['agent_trace']
                rows.append({'scenario':name,'status':run['status'],'generation_mode':run['generation_mode'],'run_id':run['run_id'],'passed':1,'latency_ms':elapsed,'transport':'TCP HTTP' if args.base_url else 'ASGI HTTP'})
                runs.append({'scenario':name,'run':run})
        down=create_app(engine=app.state.db_engine,model_service=app.state.model_service,policy_service=app.state.policy_service,knowledge_store=UnavailableGraph())
        down.state.research_services=Services(down.state,llm=GroqService(ResearchSettings(groq_api_key=None)))
        with TestClient(down) as client:
            response=client.post('/api/v2/mas/runs',json={'question':'Bệnh tiểu đường có những triệu chứng nào?'});assert response.status_code==201,response.text
            run=response.json();assert run['status']=='DEGRADED' and not run['evidence'] and run['agent_results']['knowledge']['status']=='UNAVAILABLE'
            assert client.get('/api/v2/mas/runs/'+run['run_id']).json()==run
            rows.append({'scenario':'neo4j_outage','status':run['status'],'generation_mode':run['generation_mode'],'run_id':run['run_id'],'passed':1,'latency_ms':None,'transport':'ASGI explicit graph fault injection'})
            runs.append({'scenario':'neo4j_outage','run':run})
    finally:app.state.knowledge_store.close();app.state.db_engine.dispose()
    target=ROOT/'docs/validation/diabetes_expansion';target.mkdir(parents=True,exist_ok=True)
    report={'scope':'SYNTHETIC actual API workflows; generation modes reported honestly','timestamp':datetime.now(timezone.utc).isoformat(),'code_version':source_version()[0],'rows':rows,'runs':runs}
    (target/'demo_runs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'scenarios':len(rows),'passed':sum(r['passed'] for r in rows),'generation_modes':[r['generation_mode'] for r in rows]},indent=2))

if __name__=='__main__':main()
