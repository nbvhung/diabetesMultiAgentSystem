"""Reproduce Phase 07 checks/evaluations and live browser demo, preserving actual logs.

Requires two explicitly dedicated PostgreSQL databases and a dedicated seeded Neo4j.
Starts/stops only child processes owned by this runner; no global process killing.
"""
from phase07_common import *
import os, socket, time
from urllib.request import urlopen

LOG=ROOT/'docs/validation/phase07'


def run(name,args,*,cwd=ROOT,env=None):
    started=time.perf_counter()
    process=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (LOG/f'{name}.log').write_text('COMMAND: '+subprocess.list2cmdline(args)+'\nEXIT_CODE: '+str(process.returncode)+'\n'+process.stdout+process.stderr,encoding='utf-8')
    print(f'{name}: exit {process.returncode} ({time.perf_counter()-started:.1f}s)',flush=True)
    if process.returncode:raise RuntimeError(f'{name} failed; inspect log')
    if name=='pytest' and (' skipped' in process.stdout or ' failed' in process.stdout):raise RuntimeError('Full integration validation must not skip/fail tests')
    return {'exit_code':process.returncode,'seconds':time.perf_counter()-started}


def main():
    LOG.mkdir(parents=True,exist_ok=True)
    for key in ['PHASE02_TEST_DATABASE_URL','PHASE03_TEST_DATABASE_URL','NEO4J_TEST_URI']:
        if not os.getenv(key):raise RuntimeError(f'{key} required; use dedicated disposable test services')
    if os.environ['PHASE02_TEST_DATABASE_URL']==os.environ['PHASE03_TEST_DATABASE_URL']:raise RuntimeError('Migration test database must be separate')
    os.environ['DATABASE_URL']=os.environ['PHASE03_TEST_DATABASE_URL'];os.environ['NEO4J_URI']=os.environ['NEO4J_TEST_URI'];os.environ['PYTHONUTF8']='1'
    # Freeze all model/policy artifacts. Phase 07 evaluation may not retrain or overwrite them.
    artifacts={p.relative_to(ROOT).as_posix():sha(p) for folder in ['artifacts/models','artifacts/policies'] for p in (ROOT/folder).rglob('*') if p.is_file()}
    checks={};children=[];handles=[]
    try:
        checks['pytest']=run('pytest',[sys.executable,'-m','pytest','backend/tests','-q'])
        node='node';npm='npm.cmd' if os.name=='nt' else 'npm'
        checks['frontend_unit']=run('frontend_unit',[node,'node_modules/vitest/vitest.mjs','run'],cwd=ROOT/'frontend')
        checks['frontend_build']=run('frontend_build',[npm,'run','build'],cwd=ROOT/'frontend')
        for name in ['prediction','rag','mas','rl','safety']:
            checks[name]=run(name,[sys.executable,f'scripts/evaluate_{name}.py'])
        for port in [8000,8001,5173]:
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1',port))==0:raise RuntimeError(f'Port {port} already in use; runner will not replace existing servers')
        commands=[('api',[sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000'],ROOT,8000,'/health'),
                  ('fault_api',[sys.executable,'-m','uvicorn','scripts.phase07_fault_app:knowledge_down','--factory','--host','127.0.0.1','--port','8001'],ROOT,8001,'/health'),
                  ('vite',[node,'node_modules/vite/bin/vite.js','--host','127.0.0.1','--strictPort'],ROOT/'frontend',5173,'/')]
        for name,args,cwd,port,path in commands:
            handle=(LOG/f'{name}.log').open('w',encoding='utf-8');handles.append(handle)
            child=subprocess.Popen(args,cwd=cwd,stdout=handle,stderr=subprocess.STDOUT);children.append(child)
            deadline=time.monotonic()+90
            while True:
                try:
                    with urlopen(f'http://127.0.0.1:{port}{path}',timeout=3) as response:
                        if response.status==200:break
                except Exception:
                    if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError(f'{name} did not become ready')
                    time.sleep(.2)
        checks['e2e']=run('e2e',[sys.executable,'scripts/run_e2e_demo.py','--base-url','http://127.0.0.1:8000'])
        browser_env=dict(os.environ,PHASE07_EXTERNAL_SERVERS='1')
        checks['browser']=run('browser',[node,'node_modules/@playwright/test/cli.js','test'],cwd=ROOT/'frontend',env=browser_env)
        stats=json.loads((LOG/'browser-results.json').read_text(encoding='utf-8'))['stats']
        if stats['expected']<5 or stats['skipped'] or stats['unexpected'] or stats['flaky']:
            raise RuntimeError('Browser suite must execute all five checks without skips/failures/retries')
        checks['browser_stats']=stats
        after={path:sha(ROOT/path) for path in artifacts}
        if artifacts!=after:raise RuntimeError('Frozen model/policy artifacts changed')
        from backend.app.api.experiments import read_report
        for name in ['prediction','rag','mas','rl','safety','e2e']:read_report(name)
        checks['artifacts_verified']=True
        checks['frozen_artifacts_unchanged']=True
        checks['frozen_artifact_sha256']=artifacts
        benchmark=json.loads((RES/'mas.json').read_text(encoding='utf-8'))
        safety=json.loads((RES/'safety.json').read_text(encoding='utf-8'))
        checks['benchmark_limitations']={'mas_failed_expectations':[r for r in benchmark['rows'] if not r['task_completion']], 'safety_failed_expectations':[r for r in safety['rows'] if not r['passed']]}
        checks['status']='READY_FOR_PHASE_08'
    except Exception as error:
        checks['status']='BLOCKED';checks['failure']=str(error)
        raise
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait(timeout=10)
        for handle in handles:handle.close()
        checks['timestamp']=datetime.now(timezone.utc).isoformat()
        checks['code_version']=source_version()[0]
        (LOG/'results.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print(checks['status'],flush=True)

if __name__=='__main__':main()
