"""Final verification using explicit disposable services; never rewrites metrics.

No service is implicitly installed and no remote provider quota is used. Missing
Docker is recorded as a blocked acceptance gate, not a successful deployment.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,socket,subprocess,sys,time
from datetime import datetime,timezone
from urllib.request import urlopen
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
LOG=ROOT/'docs/validation/phase08'

def execute(name,command,env,cwd=ROOT):
    started=time.perf_counter();result=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    output=result.stdout+result.stderr;(LOG/f'{name}.log').write_text(output,encoding='utf-8')
    record={'exit_code':result.returncode,'seconds':time.perf_counter()-started}
    print(name,result.returncode,flush=True)
    if name=='backend_tests':
        record['passed']=int(re.search(r'(\d+) passed',output).group(1)) if re.search(r'(\d+) passed',output) else 0
        record['skipped']=bool(re.search(r'\d+ skipped',output))
    if result.returncode:raise RuntimeError(name+' failed; see its sanitized log')
    if record.get('skipped'):raise RuntimeError('Full backend verification cannot skip tests')
    return record

def browser(env):
    children=[];handles=[]
    qa=dict(env,DIABETES_LLM_ENABLED='false',PHASE07_EXTERNAL_SERVERS='1',UI_QA_API_URL='http://127.0.0.1:18000',UI_QA_FAULT_URL='http://127.0.0.1:18001',UI_QA_BASE_URL='http://127.0.0.1:15173',UI_QA_REPORT_FILE='../docs/validation/phase08/browser-results.json',UI_QA_CAPTURE_DIR='../docs/validation/phase08')
    relative=Path(os.path.relpath(LOG,ROOT/'frontend')).as_posix()
    qa.update(UI_QA_REPORT_FILE=relative+'/browser-results.json',UI_QA_CAPTURE_DIR=relative)
    commands=[('api',[sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','18000'],ROOT,18000,'/health'),('fault_api',[sys.executable,'-m','uvicorn','scripts.phase07_fault_app:knowledge_down','--factory','--host','127.0.0.1','--port','18001'],ROOT,18001,'/health'),('vite',['node','node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','15173','--strictPort'],ROOT/'frontend',15173,'/')]
    try:
        for name,command,cwd,port,route in commands:
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1',port))==0:raise RuntimeError('Owned QA port occupied; refusing to reuse/replace a service')
            handle=(LOG/f'final-{name}.log').open('w',encoding='utf-8');handles.append(handle)
            child=subprocess.Popen(command,cwd=cwd,env=qa,stdout=handle,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0);children.append(child)
            deadline=time.monotonic()+100
            while True:
                try:
                    with urlopen(f'http://127.0.0.1:{port}{route}',timeout=2) as response:
                        if response.status==200:break
                except Exception:
                    if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Owned QA server not ready: '+name)
                    time.sleep(.3)
        result=execute('browser',['node','node_modules/@playwright/test/cli.js','test'],qa,ROOT/'frontend')
        stats=json.loads((LOG/'browser-results.json').read_text(encoding='utf-8'))['stats']
        assert stats['expected']==6 and not any(stats[k] for k in ['skipped','unexpected','flaky'])
        return {**result,'stats':stats}
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=10)
        for handle in handles:handle.close()

def main():
    global LOG
    parser=argparse.ArgumentParser();parser.add_argument('--test-env',type=Path);parser.add_argument('--stages',nargs='+',choices=['backend','frontend','browser','integrity','compose'],default=['backend','frontend','browser','integrity','compose']);parser.add_argument('--compose-cli');args=parser.parse_args()
    LOG=Path(os.getenv('DIABETES_CHECK_OUTPUT',str(LOG)))
    LOG.mkdir(parents=True,exist_ok=True)
    env={**os.environ,**{k:v for k,v in (dotenv_values(args.test_env) if args.test_env else {}).items() if v is not None},'PYTHONUTF8':'1','GROQ_API_KEY':'','DIABETES_LLM_ENABLED':'true'}
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'status':'RUNNING','checks':{},'remote_llm_calls':0,'training_rerun':False}
    try:
        if set(args.stages)&{'backend','browser'}:
            from sqlalchemy.engine import make_url
            original=dotenv_values(ROOT/'.env')
            for name in ['PHASE02_TEST_DATABASE_URL','PHASE03_TEST_DATABASE_URL','NEO4J_TEST_URI']:
                if not env.get(name):raise RuntimeError('Explicit disposable service required: '+name)
            urls=[make_url(env[k]) for k in ['PHASE02_TEST_DATABASE_URL','PHASE03_TEST_DATABASE_URL']]
            if urls[0]==urls[1] or any(url==make_url(original['DATABASE_URL']) for url in urls):raise RuntimeError('Tests must not target the application database')
            if env['NEO4J_TEST_URI']==original.get('NEO4J_URI'):raise RuntimeError('Tests require a separate Neo4j instance')
            env['DATABASE_URL']=env['PHASE03_TEST_DATABASE_URL'];env['NEO4J_URI']=env['NEO4J_TEST_URI']
        if 'backend' in args.stages:
            result['checks']['migration']=execute('migration',[sys.executable,'-m','alembic','upgrade','head'],env)
            result['checks']['initialize']=execute('initialize',[sys.executable,'scripts/bootstrap_demo.py'],env)
            result['checks']['backend']=execute('backend_tests',[sys.executable,'-m','pytest','backend/tests','-q'],env)
        if 'frontend' in args.stages:
            result['checks']['frontend_unit']=execute('frontend_unit',['node','node_modules/vitest/vitest.mjs','run'],env,ROOT/'frontend')
            result['checks']['frontend_build']=execute('frontend_build',['npm.cmd' if os.name=='nt' else 'npm','run','build'],env,ROOT/'frontend')
        if 'browser' in args.stages:result['checks']['browser']=browser(env)
        if 'integrity' in args.stages:
            previous=json.loads((ROOT/'docs/validation/phase07/results.json').read_text(encoding='utf-8'))['frozen_artifact_sha256']
            for name,digest in previous.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
            sys.path.insert(0,str(ROOT))
            from backend.app.api.experiments import read_report
            names=['prediction','rl','diabetes_rag','diabetes_mas','diabetes_safety','diabetes_llm']
            for name in names:read_report(name)
            result['checks']['integrity']={'frozen_artifacts_unchanged':True,'verified_measured_bundles':names}
        if 'compose' in args.stages:
            executable=args.compose_cli or shutil.which('docker')
            if not executable:result['checks']['compose']={'status':'BLOCKED_NO_DOCKER_CLI_ENGINE'}
            else:
                prefix=[executable] if args.compose_cli else [executable,'compose']
                result['checks']['compose_config']=execute('compose_config',prefix+['--env-file','.env.compose','-f','compose.yaml','config','--quiet'],env)
                attempt=subprocess.run(prefix+['--env-file','.env.compose','-f','compose.yaml','up','--build','--wait'],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
                (LOG/'compose_startup.log').write_text(attempt.stdout+attempt.stderr,encoding='utf-8')
                result['checks']['compose']={'exit_code':attempt.returncode,'status':'STARTED_NEEDS_WORKFLOW_CHECK' if not attempt.returncode else 'BLOCKED_RUNTIME'}
        result['status']='BLOCKED' if any('BLOCKED' in str(check.get('status','')) for check in result['checks'].values()) else 'REQUESTED_CHECKS_PASSED_NOT_FULL_ACCEPTANCE'
    except Exception as error:result['status']='BLOCKED';result['error_type']=type(error).__name__;raise
    finally:
        (LOG/'final_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result['status'])
    if result['status']=='BLOCKED':raise SystemExit(1)

if __name__=='__main__':main()
