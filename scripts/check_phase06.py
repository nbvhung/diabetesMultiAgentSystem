"""Phase 06 end-to-end reproducibility, actual training/eval/tests and API integration."""
from pathlib import Path
import os,subprocess,sys,json,asyncio
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));LOG=ROOT/'docs/validation/phase06_fixes';LOG.mkdir(parents=True,exist_ok=True)
for key in ['PHASE02_TEST_DATABASE_URL','PHASE03_TEST_DATABASE_URL','NEO4J_TEST_URI']:assert os.getenv(key),key+' required (dedicated test services)'
assert os.environ['PHASE02_TEST_DATABASE_URL']!=os.environ['PHASE03_TEST_DATABASE_URL']
os.environ['DATABASE_URL']=os.environ['PHASE03_TEST_DATABASE_URL'];os.environ['NEO4J_URI']=os.environ['NEO4J_TEST_URI']
checks={}
commands=[]
if '--execute-notebook' in sys.argv:
 commands.append(('notebook',[sys.executable,'-m','jupyter','nbconvert','--to','notebook','--execute','--inplace','notebooks/04_rl_q_learning_training.ipynb','--ExecutePreprocessor.timeout=600']))
else:
 assert 'EXIT_CODE: 0' in (LOG/'notebook.log').read_text(),'Execute notebook first or pass --execute-notebook'
 checks['prior_notebook_execution_verified']=True
commands.extend([('evaluation',[sys.executable,'scripts/evaluate_rl.py']),('pytest',[sys.executable,'-m','pytest','backend/tests','-v'])])
for name,args in commands:
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (LOG/(name+'.log')).write_text('COMMAND: '+subprocess.list2cmdline(args)+'\nEXIT_CODE: '+str(p.returncode)+'\n'+p.stdout+p.stderr,encoding='utf-8')
 checks[name]=p.returncode==0 and (' skipped' not in p.stdout if name=='pytest' else True)
 print(name,checks[name],flush=True)
 if not checks[name]:sys.exit(1)
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.rl.policy import PolicyService
from backend.app.rl.mdp import ACTIONS
app=create_app();records=[]
base=dict(pregnancies=0,glucose=100,blood_pressure=70,skin_thickness=20,insulin=50,bmi=22,diabetes_pedigree=.3,age=30)
with TestClient(app) as client:
 for label,body in [('SYNTHETIC_EDUCATION',{'question':'What diabetes symptoms include thirst?'}),('SYNTHETIC_ASSESSMENT',{'assessment':base,'is_synthetic':True}),('SYNTHETIC_SAFETY_VETO',{'question':'Prescribe insulin'})]:
  response=client.post('/api/v1/mas/runs',json=body);assert response.status_code==201,response.text
  run=response.json();rl=run['agent_results']['rl']
  if label.endswith('VETO'):
   assert rl['status']=='SKIPPED' and run['status']=='BLOCKED'
  else:
   assert rl['status']=='COMPLETED' and rl['implementation']=='integrated'
   assert rl['output']['decision_source']=='policy' and rl['output']['policy_version']=='education-q-1.1'
   assert rl['output']['action'] in ACTIONS
   education=run['agent_results']['education']['output']
   assert education['proposed_action']==rl['output']['action']
   assert education['effective_action'] in ACTIONS
   if education['proposed_action']!=education['effective_action']:assert education['override_reason']
   assert any(e['effective_action']==education['effective_action'] and e['proposed_action']==education['proposed_action'] for e in run['agent_trace'])
   assert any(e['policy_version']==rl['output']['policy_version'] and e['action']==rl['output']['action'] and e['decision_source']=='policy' for e in run['agent_trace'])
  assert client.get('/api/v1/mas/runs/'+run['run_id']).json()==run
  records.append({'case':label,'run':run})
service=app.state.policy_service; before=service.q.copy()
async def concurrent():
 import httpx
 async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://synthetic-test') as client:
  results=await asyncio.gather(*(client.post('/api/v1/mas/runs',json={'question':'What diabetes symptoms are described?'}) for _ in range(4)))
  assert all(r.status_code==201 for r in results)
  runs=[r.json() for r in results]
  assert len({r['run_id'] for r in runs})==4
  assert all(all(e['run_id']==r['run_id'] for e in r['agent_trace']) for r in runs)
asyncio.run(concurrent())
import numpy as np
np.testing.assert_array_equal(before,service.q)
fallback_app=create_app(engine=app.state.db_engine,knowledge_store=app.state.knowledge_store,policy_service=PolicyService(ROOT/'.tools/phase06-intentionally-absent-policy'))
with TestClient(fallback_app) as client:
 result=client.post('/api/v1/mas/runs',json={'question':'What diabetes symptoms are described?'});assert result.status_code==201,result.text
 run=result.json();decision=run['agent_results']['rl']['output']
 assert decision['decision_source']=='fallback' and decision['policy_version']=='fallback-rule-1.0'
 assert decision['state']['decision_reason']=='POLICY_UNAVAILABLE'
 records.append({'case':'SYNTHETIC_NO_ARTIFACT_FALLBACK','run':run})
(LOG/'api_workflows.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
checks.update({'proposed_effective_actions_persisted':True,'api_rl_policy_and_trace':True,'safety_veto':True,'missing_policy_explicit_fallback':True,'concurrent_requests':4,'q_table_not_updated_by_requests':True})
(LOG/'results.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
app.state.knowledge_store.close();app.state.db_engine.dispose();print(checks)
