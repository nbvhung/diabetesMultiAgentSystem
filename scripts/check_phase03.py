"""Require real dedicated PostgreSQL; execute tests, synthetic demo and live HTTP."""
import json,os,subprocess,sys,socket,time
from pathlib import Path
from urllib.request import urlopen,Request
ROOT=Path(__file__).resolve().parents[1]; LOG=ROOT/'docs/validation/phase03';LOG.mkdir(parents=True,exist_ok=True)
assert os.getenv('PHASE03_TEST_DATABASE_URL') and os.getenv('PHASE02_TEST_DATABASE_URL'), 'Set two dedicated test database URLs; no skips accepted'
assert os.environ['PHASE02_TEST_DATABASE_URL']!=os.environ['PHASE03_TEST_DATABASE_URL'],'Use separate disposable test databases'
os.environ['DATABASE_URL']=os.environ['PHASE03_TEST_DATABASE_URL']
checks={}
for name,args in [('pytest',[sys.executable,'-m','pytest','backend/tests','-v']),('demo',[sys.executable,'scripts/demo_prediction.py'])]:
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (LOG/(name+'.log')).write_text('COMMAND: '+subprocess.list2cmdline(args)+'\nEXIT_CODE: '+str(p.returncode)+'\n'+p.stdout+p.stderr,encoding='utf-8'); checks[name]=p.returncode==0 and (name!='pytest' or ' skipped' not in p.stdout)
 print(name,checks[name],flush=True)
 if not checks[name]: sys.exit(1)
with socket.socket() as s:
 s.bind(('127.0.0.1',0));port=s.getsockname()[1]
with (LOG/'uvicorn.log').open('w',encoding='utf-8') as log:
 p=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 try:
  def get(path):
   with urlopen(f'http://127.0.0.1:{port}'+path,timeout=40) as response: return json.load(response)
  deadline=time.monotonic()+40
  while True:
   try: health=get('/health');break
   except Exception:
    if time.monotonic()>deadline or p.poll() is not None: raise
    time.sleep(.2)
  model=get('/api/v1/models/current')
  demo=json.loads((LOG/'demo.json').read_text())[0]
  prior=get('/api/v1/mas/runs/'+demo['run_id'])
  assert prior['agent_results']['prediction']['output']['persisted_record_id']==demo['persisted_record_id']
  trace=get('/api/v1/mas/runs/'+demo['run_id']+'/trace')
  assert trace['agent_trace']==prior['agent_trace']
  (LOG/'live_http.json').write_text(json.dumps({'health':health,'model':model,'prior_run_from_new_process':prior,'trace':trace},indent=2),encoding='utf-8')
  checks['live_http_restart_readback']=True
 finally:
  p.terminate();p.wait(timeout=10)
(LOG/'results.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(checks,flush=True)
