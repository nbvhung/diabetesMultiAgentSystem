"""Start/status/stop only this project's built-frontend gateway and quick tunnel."""
import argparse,json,os,re,secrets,shutil,socket,subprocess,sys,time
from pathlib import Path
from dotenv import dotenv_values
import psutil
import httpx

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.tools/phase08/demo'
ENV=ROOT/'.env.demo'
MARKER='backend.app.demo_gateway:create_gateway'

def alive(pid,part):
    try:return part in ' '.join(psutil.Process(pid).cmdline())
    except (psutil.NoSuchProcess,psutil.AccessDenied):return False

def status():
    info=json.loads((STATE/'state.json').read_text()) if (STATE/'state.json').exists() else {}
    return {**info,'gateway_running':alive(info.get('gateway_pid',0),MARKER),'tunnel_running':alive(info.get('tunnel_pid',0),'cloudflared')}

def start(tunnel):
    STATE.mkdir(parents=True,exist_ok=True)
    current=status()
    if current['gateway_running'] or current['tunnel_running']:raise RuntimeError('A project demo process already runs; use status or stop first')
    if not ENV.exists():ENV.write_text('DEMO_ACCESS_PASSWORD='+secrets.token_urlsafe(24)+'\nDEMO_UPSTREAM=http://127.0.0.1:8000\n',encoding='utf-8')
    settings=dotenv_values(ENV)
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',8082))==0:raise RuntimeError('Port 8082 is occupied; no service replaced')
    with httpx.Client(timeout=10,trust_env=False) as client:client.get(settings['DEMO_UPSTREAM']+'/health').raise_for_status()
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    env=dict(os.environ,**{k:v for k,v in settings.items() if v is not None},PYTHONUTF8='1')
    handle=(STATE/'gateway.log').open('w',encoding='utf-8')
    command=[sys.executable,'-m','uvicorn',MARKER,'--factory','--host','127.0.0.1','--port','8082']
    process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=handle,stderr=subprocess.STDOUT,creationflags=flags)
    info={'gateway_pid':process.pid,'local_url':'http://127.0.0.1:8082','credentials_file':'.env.demo','username':'demo','public_url':None,'tunnel_pid':0}
    (STATE/'state.json').write_text(json.dumps(info,indent=2))
    try:
        deadline=time.monotonic()+45
        while True:
            try:
                with httpx.Client(timeout=3,trust_env=False,auth=('demo',settings['DEMO_ACCESS_PASSWORD'])) as client:client.get(info['local_url']).raise_for_status()
                break
            except httpx.HTTPError:
                if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Gateway startup failed; inspect .tools/phase08/demo/gateway.log')
                time.sleep(.3)
        if tunnel:
            executable=shutil.which('cloudflared') or str(ROOT/'.tools/phase08/cloudflared.exe')
            if not Path(executable).is_file():raise RuntimeError('Install official cloudflared first; see docs/deployment.md')
            tunnel_log=(STATE/'tunnel.log').open('w',encoding='utf-8')
            child=subprocess.Popen([executable,'tunnel','--url',info['local_url'],'--protocol','http2','--no-autoupdate'],cwd=ROOT,stdout=tunnel_log,stderr=subprocess.STDOUT,creationflags=flags)
            info['tunnel_pid']=child.pid
            (STATE/'state.json').write_text(json.dumps(info,indent=2))
            deadline=time.monotonic()+45
            while True:
                text=(STATE/'tunnel.log').read_text(encoding='utf-8',errors='replace')
                match=re.search(r'https://[a-z0-9-]+\.trycloudflare\.com',text)
                if match:info['public_url']=match.group(0);break
                if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Tunnel did not issue a URL; local gateway still works; inspect tunnel.log')
                time.sleep(.4)
        (STATE/'state.json').write_text(json.dumps(info,indent=2))
        print(json.dumps({**info,'note':'Password remains in ignored .env.demo. A tunnel URL is not a verified cloud deployment.'},indent=2))
    finally:handle.close()

def stop():
    info=status()
    for key,marker in [('tunnel_pid','cloudflared'),('gateway_pid',MARKER)]:
        if alive(info.get(key,0),marker):
            process=psutil.Process(info[key]);process.terminate()
            try:process.wait(10)
            except psutil.TimeoutExpired:raise RuntimeError('Owned demo process did not stop')
    print('Stopped only verified project demo processes; API, PostgreSQL and Neo4j retained.')

def restart_gateway():
    info=status()
    if not info['gateway_running']:raise RuntimeError('No owned gateway is running; use start instead')
    process=psutil.Process(info['gateway_pid']);process.terminate();process.wait(10)
    values={k:v for k,v in dotenv_values(ENV).items() if v is not None}
    with (STATE/'gateway.log').open('a',encoding='utf-8') as handle:
        child=subprocess.Popen([sys.executable,'-m','uvicorn',MARKER,'--factory','--host','127.0.0.1','--port','8082'],cwd=ROOT,env={**os.environ,**values},stdout=handle,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    info['gateway_pid']=child.pid
    info.pop('gateway_running',None);info.pop('tunnel_running',None)
    (STATE/'state.json').write_text(json.dumps(info,indent=2))
    print('Owned gateway restarted; existing tunnel and backend retained.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['start','status','stop','restart-gateway']);parser.add_argument('--tunnel',action='store_true');args=parser.parse_args()
    if args.action=='start':start(args.tunnel)
    elif args.action=='stop':stop()
    elif args.action=='restart-gateway':restart_gateway()
    else:print(json.dumps(status(),indent=2))
