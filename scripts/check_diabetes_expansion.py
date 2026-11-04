"""Reproducible offline research checks plus optional explicitly bounded live Groq validation."""
from phase07_common import *
import argparse,os,socket,time
from urllib.request import urlopen

LOG=ROOT/'docs/validation/diabetes_expansion'


def run(name,args,*,cwd=ROOT,env=None):
    started=time.perf_counter();process=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (LOG/f'{name}.log').write_text('COMMAND: '+subprocess.list2cmdline(args)+'\nEXIT_CODE: '+str(process.returncode)+'\n'+process.stdout+process.stderr,encoding='utf-8')
    print(f'{name}: exit {process.returncode} ({time.perf_counter()-started:.1f}s)',flush=True)
    if process.returncode:raise RuntimeError(f'{name} failed; inspect actual log')
    if name=='pytest' and (' skipped' in process.stdout or ' failed' in process.stdout):raise RuntimeError('Integration check cannot skip/fail tests')
    return {'exit_code':process.returncode,'seconds':time.perf_counter()-started}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live-llm',action='store_true');args=parser.parse_args()
    LOG.mkdir(parents=True,exist_ok=True)
    for name in ['PHASE02_TEST_DATABASE_URL','PHASE03_TEST_DATABASE_URL','NEO4J_TEST_URI']:
        if not os.getenv(name):raise RuntimeError(name+' required; dedicated disposable test services only')
    if os.environ['PHASE02_TEST_DATABASE_URL']==os.environ['PHASE03_TEST_DATABASE_URL']:raise RuntimeError('Migration DB must be separate')
    os.environ['DATABASE_URL']=os.environ['PHASE03_TEST_DATABASE_URL'];os.environ['NEO4J_URI']=os.environ['NEO4J_TEST_URI'];os.environ['PYTHONUTF8']='1'
    frozen={p.relative_to(ROOT).as_posix():sha(p) for folder in ['artifacts/models','artifacts/policies'] for p in (ROOT/folder).rglob('*') if p.is_file()}
    checks={};children=[];handles=[]
    try:
        # Preparation is explicit and offline; fetch/download have separate commands.
        from backend.app.research.corpus import Corpus
        corpus=Corpus();corpus.load();checks['corpus']={k:corpus.manifest[k] for k in ['dataset_version','source_count','chunk_count','chunks_sha256']}
        checks['seed']=run('seed',[sys.executable,'scripts/seed_diabetes_graph.py'])
        checks['pytest']=run('pytest',[sys.executable,'-m','pytest','backend/tests','-q'])
        checks['frontend_unit']=run('frontend_unit',['node','node_modules/vitest/vitest.mjs','run'],cwd=ROOT/'frontend')
        checks['frontend_build']=run('frontend_build',['npm.cmd' if os.name=='nt' else 'npm','run','build'],cwd=ROOT/'frontend')
        for name in ['rag','mas','safety']:
            checks['diabetes_'+name]=run('diabetes_'+name,[sys.executable,f'scripts/evaluate_diabetes_{name}.py'])
        checks['llm_status']=run('llm_status',[sys.executable,'scripts/evaluate_diabetes_llm.py',*(['--live','--limit','6'] if args.live_llm else [])])
        for port in [8000,8001,5173]:
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1',port))==0:raise RuntimeError(f'Port {port} in use; no existing process will be replaced')
        # Browser/offline demos never spend a user's remote quota implicitly. A live
        # provider evaluation is a separate --live-llm step with a six-question cap.
        server_env=dict(os.environ,DIABETES_LLM_ENABLED='false')
        commands=[('api',[sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000'],ROOT,8000,'/health'),
                  ('fault_api',[sys.executable,'-m','uvicorn','scripts.phase07_fault_app:knowledge_down','--factory','--host','127.0.0.1','--port','8001'],ROOT,8001,'/health'),
                  ('vite',['node','node_modules/vite/bin/vite.js','--host','127.0.0.1','--strictPort'],ROOT/'frontend',5173,'/')]
        for name,command,cwd,port,path in commands:
            handle=(LOG/f'{name}.log').open('w',encoding='utf-8');handles.append(handle)
            child=subprocess.Popen(command,cwd=cwd,env=server_env,stdout=handle,stderr=subprocess.STDOUT);children.append(child)
            deadline=time.monotonic()+100
            while True:
                try:
                    with urlopen(f'http://127.0.0.1:{port}{path}',timeout=3) as response:
                        if response.status==200:break
                except Exception:
                    if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError(name+' failed to become ready')
                    time.sleep(.2)
        checks['demo']=run('demo',[sys.executable,'scripts/run_diabetes_demo.py','--base-url','http://127.0.0.1:8000'],env=server_env)
        checks['browser']=run('browser',['node','node_modules/@playwright/test/cli.js','test'],cwd=ROOT/'frontend',env=dict(server_env,PHASE07_EXTERNAL_SERVERS='1'))
        stats=json.loads((LOG/'browser-results.json').read_text(encoding='utf-8'))['stats']
        if stats['expected']<6 or stats['skipped'] or stats['unexpected'] or stats['flaky']:raise RuntimeError('All six browser scenarios must pass without skips/retries')
        checks['browser_stats']=stats
        if any(sha(ROOT/path)!=digest for path,digest in frozen.items()):raise RuntimeError('Frozen DL/RL artifact modified')
        checks['frozen_artifacts_unchanged']=True;checks['frozen_artifact_sha256']=frozen
        from backend.app.api.experiments import read_report
        for name in ['diabetes_rag','diabetes_mas','diabetes_safety']:read_report(name)
        checks['measured_artifacts_verified']=True
        live=json.loads((LOG/'llm_live_status.json').read_text(encoding='utf-8'))
        checks['live_llm']=live
        checks['status']='IMPLEMENTED_LIVE_LLM_VERIFIED' if live['status']=='LIVE_EXECUTED' else 'IMPLEMENTED_PENDING_LIVE_LLM_VALIDATION'
    except Exception as error:
        checks['status']='BLOCKED_CHECK_FAILURE';checks['failure']=str(error);raise
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=10)
        for handle in handles:handle.close()
        checks['timestamp']=datetime.now(timezone.utc).isoformat();checks['code_version']=source_version()[0]
        (LOG/'results.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(checks['status'],flush=True)

if __name__=='__main__':main()
