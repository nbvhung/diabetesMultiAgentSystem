"""One-command native release: own API, built UI, authenticated gateway.

Requires configured PostgreSQL and trusted artifacts; Windows Neo4j can be
started through the existing local manager. No other API process is replaced.
"""
from pathlib import Path
import argparse,json,os,socket,subprocess,sys,time
from dotenv import dotenv_values,set_key
import httpx,psutil

ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'.tools/final-demo';PORT=18082
def owned(info):
    try:
        process=psutil.Process(info['pid'])
        return process if str(PORT) in process.cmdline() and 'backend.app.main:app' in process.cmdline() and Path(process.cwd()).resolve()==ROOT else None
    except (KeyError,psutil.Error):return None
def state():return json.loads((STATE/'state.json').read_text()) if (STATE/'state.json').exists() else {}
def run(command):subprocess.run(command,cwd=ROOT,check=True)
def start(tunnel):
    STATE.mkdir(parents=True,exist_ok=True)
    if owned(state()):print('Final demo API already running. Use status or stop.');return
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',PORT))==0:raise RuntimeError('Final demo port occupied; existing service preserved')
    if os.name=='nt':run([sys.executable,'scripts/local_neo4j.py','start'])
    run([sys.executable,'scripts/bootstrap_demo.py'])
    run(['npm.cmd' if os.name=='nt' else 'npm','--prefix','frontend','run','build'])
    with (STATE/'api.log').open('w',encoding='utf-8') as output:
        process=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port',str(PORT)],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    (STATE/'state.json').write_text(json.dumps({'pid':process.pid,'api_port':PORT}))
    deadline=time.monotonic()+90
    try:
        while True:
            try:
                with httpx.Client(timeout=3,trust_env=False) as client:client.get(f'http://127.0.0.1:{PORT}/health').raise_for_status()
                break
            except httpx.HTTPError:
                if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('API startup failed; inspect .tools/final-demo/api.log')
                time.sleep(.3)
        # The existing gateway manager verifies process ownership before restart.
        sys.path.insert(0,str(ROOT/'scripts'));import demo_host
        current=demo_host.status()
        if not (ROOT/'.env.demo').exists():
            import secrets
            (ROOT/'.env.demo').write_text('DEMO_ACCESS_PASSWORD='+secrets.token_urlsafe(24)+'\n',encoding='utf-8')
        set_key(ROOT/'.env.demo','DEMO_UPSTREAM',f'http://127.0.0.1:{PORT}')
        if current['gateway_running']:demo_host.restart_gateway()
        else:demo_host.start(tunnel)
        print('Final web: http://127.0.0.1:8082 ; user demo; password remains in .env.demo')
    except Exception:
        if owned(state()):process.terminate()
        raise
def stop():
    run([sys.executable,'scripts/demo_host.py','stop'])
    process=owned(state())
    if process:process.terminate();process.wait(15)
    print('Only owned demo API/gateway stopped. PostgreSQL/Neo4j preserved.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['start','status','stop']);parser.add_argument('--tunnel',action='store_true');args=parser.parse_args()
    if args.action=='start':start(args.tunnel)
    elif args.action=='stop':stop()
    else:
        print(json.dumps({'api_running':bool(owned(state())),'local_url':'http://127.0.0.1:8082','username':'demo','credentials_file':'.env.demo'}));run([sys.executable,'scripts/demo_host.py','status'])
