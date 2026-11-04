from pathlib import Path
import json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
LOG=ROOT/'docs/validation/phase04';LOG.mkdir(parents=True,exist_ok=True)
for key in ['NEO4J_TEST_URI','PHASE02_TEST_DATABASE_URL','PHASE03_TEST_DATABASE_URL']: assert os.getenv(key),key+' required (dedicated DBs)'
os.environ['NEO4J_URI']=os.environ['NEO4J_TEST_URI'];os.environ['DATABASE_URL']=os.environ['PHASE03_TEST_DATABASE_URL']
checks={}
for name,args in [('seed',[sys.executable,'scripts/seed_knowledge.py']),('evaluation',[sys.executable,'scripts/evaluate_knowledge.py']),('pytest',[sys.executable,'-m','pytest','backend/tests','-v'])]:
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (LOG/(name+'.log')).write_text('COMMAND: '+subprocess.list2cmdline(args)+'\nEXIT_CODE: '+str(p.returncode)+'\n'+p.stdout+p.stderr,encoding='utf-8')
 checks[name]=p.returncode==0 and (' skipped' not in p.stdout if name=='pytest' else True)
 print(name,checks[name],flush=True)
 if not checks[name]:sys.exit(1)
from fastapi.testclient import TestClient
from backend.app.main import create_app
with TestClient(create_app()) as client:
 response=client.post('/api/v1/mas/runs',json={'question':'What diabetes symptoms include thirst? Please cite sources.'})
 assert response.status_code==201,response.text
 run=response.json();assert run['evidence'] and run['agent_results']['knowledge']['implementation']=='integrated'
 assert all(e['evidence_id'] in run['response'] for e in run['evidence'])
 assert client.get('/api/v1/mas/runs/'+run['run_id']).json()==run
 assert client.get('/api/v1/knowledge/health').status_code==200
 (LOG/'api_workflow.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
checks['postgres_api_workflow_citations']=True
(LOG/'results.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(checks)
