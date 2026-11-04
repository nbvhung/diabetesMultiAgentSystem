"""Personal Windows Neo4j instance, separate from disposable QA databases.

Uses installed Neo4j 5.26 binaries. Mutable files use an ASCII-only local folder
because this Windows launcher cannot resolve this workspace's Unicode path.
Secrets stay in ignored .env; commands never print them or use shell interpolation.
"""
import argparse,json,os,secrets,shutil,socket,subprocess,sys,time
from pathlib import Path
from hashlib import sha256
from dotenv import dotenv_values,set_key
from neo4j import GraphDatabase

ROOT=Path(__file__).resolve().parents[1]
STATE=Path(os.getenv('DIABETES_NEO4J_DATA',r'D:\diabetes-mas-local\neo4j')).resolve()
CONF=STATE/'conf'
MARKER='-Ddiabetes.mas.local.neo4j='+sha256(str(STATE.resolve()).encode()).hexdigest()[:20]
URI='bolt://127.0.0.1:7687'


def configuration():
    values=dotenv_values(ROOT/'.env')
    password=values.get('NEO4J_PASSWORD') or ''
    if values.get('NEO4J_USER')!='neo4j' or len(password)<8 or password.startswith('REPLACE_'):
        raise RuntimeError('Run setup first; local Neo4j credentials are not configured')
    return values,password


def paths(home=None,java_home=None):
    saved=json.loads((STATE/'initialized.json').read_text(encoding='utf-8')) if (STATE/'initialized.json').exists() else {}
    # This installed Windows Java launcher cannot expand a wildcard classpath
    # under a non-ASCII installation path. Reuse the existing ASCII binary path;
    # the separate configuration and database files use an ASCII data directory.
    choices=[home,saved.get('home'),os.getenv('NEO4J_HOME'),r'D:\TEMP\diabetes-neo4j-phase04\neo4j-community-5.26.0',str(ROOT/'.tools/neo4j/neo4j-community-5.26.0')]
    installation=next((Path(p).resolve() for p in choices if p and (Path(p)/'lib').is_dir()),None)
    java_choices=[java_home,saved.get('java_home'),r'C:\Program Files\Java\jdk-17',os.getenv('JAVA_HOME')]
    java=next((Path(p)/'bin/java.exe' for p in java_choices if p and (Path(p)/'bin/java.exe').is_file()),None)
    if installation is None or java is None:raise RuntimeError('Neo4j 5.26 / Java 17 installation not found; specify --home and --java-home')
    environment=dict(os.environ,NEO4J_HOME=str(installation),NEO4J_CONF=str(CONF),JAVA_HOME=str(java.parent.parent))
    return installation,java,environment


def command(home,java,kind,*args):
    entry='org.neo4j.server.startup.'+('Neo4jAdminCommand' if kind=='admin' else 'Neo4jCommand')
    return [str(java),'-Dfile.encoding=UTF-8','-Dbasedir='+str(home),MARKER,'-cp',str(home/'lib/*'),entry,*args]


def owned_processes():
    # Match an exact project-specific JVM argument, not every java.exe on the PC.
    import psutil
    result=[]
    for process in psutil.process_iter(['name','cmdline']):
        try:
            if (process.info['name'] or '').lower()=='java.exe' and MARKER in (process.info['cmdline'] or []):result.append(process)
        except (psutil.NoSuchProcess,psutil.AccessDenied):continue
    children=[]
    for process in result:
        try:children.extend(p for p in process.children(recursive=True) if p.name().lower()=='java.exe')
        except (psutil.NoSuchProcess,psutil.AccessDenied):continue
    return list({p.pid:p for p in result+children}.values())


def occupied(port):
    with socket.socket() as sock:
        sock.settimeout(.4)
        return sock.connect_ex(('127.0.0.1',port))==0


def verify():
    _,password=configuration()
    with GraphDatabase.driver(URI,auth=('neo4j',password),connection_timeout=2,max_transaction_retry_time=0) as driver:
        driver.verify_connectivity()
        with driver.session(database='neo4j') as session:
            assert session.run('RETURN 1 AS ok').single()['ok']==1
    return {'status':'available','uri':URI,'browser':'http://127.0.0.1:7474/browser/','authentication':'enabled','user':'neo4j'}


def setup(home,java,environment):
    if owned_processes():raise RuntimeError('Stop this local instance before setup')
    STATE.mkdir(parents=True,exist_ok=True);CONF.mkdir(exist_ok=True)
    for directory in ['data','logs','run','import','plugins','transactions']:(STATE/directory).mkdir(exist_ok=True)
    for name in ['server-logs.xml','user-logs.xml','neo4j-admin.conf']:
        if (home/'conf'/name).is_file() and not (CONF/name).exists():shutil.copyfile(home/'conf'/name,CONF/name)
    entries={
        'server.default_listen_address':'127.0.0.1','server.default_advertised_address':'127.0.0.1',
        'server.bolt.listen_address':'127.0.0.1:7687','server.bolt.advertised_address':'127.0.0.1:7687',
        'server.http.listen_address':'127.0.0.1:7474','server.http.advertised_address':'127.0.0.1:7474',
        'server.https.enabled':'false','dbms.security.auth_enabled':'true',
        'server.memory.heap.initial_size':'256m','server.memory.heap.max_size':'512m','server.memory.pagecache.size':'128m',
        **{'server.directories.'+name:(STATE/name).as_posix() for name in ['data','logs','run','import','plugins']},
        'server.directories.transaction.logs.root':(STATE/'transactions').as_posix(),
        'server.jvm.additional':MARKER,
    }
    # neo4j.conf uses Java Properties ISO-8859-1 parsing. Preserve Vietnamese
    # workspace paths with standard Unicode escapes instead of UTF-8 mojibake.
    prop=lambda value:''.join('\\u'+format(ord(c),'04x') if ord(c)>127 else c for c in value)
    (CONF/'neo4j.conf').write_text('\n'.join(k+'='+prop(v) for k,v in entries.items())+'\n',encoding='ascii')
    before=dotenv_values(ROOT/'.env');password=before.get('NEO4J_PASSWORD') or ''
    initialized=(STATE/'initialized.json').exists()
    if initialized:
        configuration()  # Never reset an existing database password by rewriting .env.
    else:
        if before.get('NEO4J_USER') not in (None,'','neo4j','REPLACE_USER'):raise RuntimeError('This new local instance uses user neo4j; custom configured user was preserved')
        if len(password)<8 or password.startswith(('REPLACE_','YOUR_')):password=secrets.token_urlsafe(24)
        for key,value in {'NEO4J_URI':URI,'NEO4J_USER':'neo4j','NEO4J_PASSWORD':password}.items():
            set_key(ROOT/'.env',key,value,quote_mode='always')
        after=dotenv_values(ROOT/'.env')
        assert all(before.get(key)==after.get(key) for key in ['GROQ_API_KEY','DATABASE_URL','POSTGRES_PASSWORD'])
        process=subprocess.run(command(home,java,'admin','dbms','set-initial-password',password),env=environment,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
        if process.returncode:
            # Do not expose the full invocation/exception, which has a password argument.
            (STATE/'setup-error.log').write_text((process.stdout+process.stderr).replace(password,'[REDACTED]'),encoding='utf-8')
            raise RuntimeError('Initial Neo4j setup failed; see '+str(STATE/'setup-error.log'))
        (STATE/'initialized.json').write_text(json.dumps({'home':str(home),'java_home':str(java.parent.parent),'marker':MARKER}),encoding='utf-8')
    return {'status':'configured','uri':URI,'authentication':'enabled','credentials_file':'.env','groq_and_postgresql_preserved':True}


def start(home,java,environment):
    if not (STATE/'initialized.json').exists():raise RuntimeError('Run setup successfully before start')
    configuration()
    if owned_processes():return verify()
    if occupied(7474) or occupied(7687):raise RuntimeError('7474/7687 is occupied; no existing service will be replaced')
    with (STATE/'console.log').open('a',encoding='utf-8') as output:
        # A hidden background JVM with file output, no GUI windows or inherited pipes.
        process=subprocess.Popen(command(home,java,'server','console'),env=environment,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+75
    while time.monotonic()<deadline:
        try:return verify()
        except Exception:
            if process.poll() is not None:raise RuntimeError('Neo4j failed to start; inspect '+str(STATE/'console.log')) from None
            time.sleep(.5)
    raise RuntimeError('Neo4j startup timed out; inspect local logs')


def stop(home,java,environment):
    processes=owned_processes()
    if not processes:return {'status':'stopped','owned_processes':0}
    # Official stop handles supported hosts gracefully; Windows console deployments
    # may require terminating only the JVMs with this exact ownership marker.
    if (STATE/'initialized.json').exists():
        try:
            subprocess.run(command(home,java,'server','stop'),env=environment,cwd=ROOT,capture_output=True,timeout=20)
        except subprocess.TimeoutExpired:pass
    import psutil
    remaining=owned_processes()
    for process in remaining:
        try:process.terminate()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(remaining,timeout=10)
    if owned_processes():raise RuntimeError('Owned Neo4j process has not stopped')
    return {'status':'stopped','owned_processes':len(processes)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['setup','start','status','stop']);parser.add_argument('--home');parser.add_argument('--java-home');args=parser.parse_args()
    try:
        home,java,environment=paths(args.home,args.java_home)
        result=setup(home,java,environment) if args.action=='setup' else start(home,java,environment) if args.action=='start' else stop(home,java,environment) if args.action=='stop' else verify()
        print(json.dumps(result,indent=2))
    except Exception as error:
        if isinstance(error,RuntimeError):print(str(error),file=sys.stderr)
        else:print('Neo4j local operation failed ('+type(error).__name__+'); credentials were not printed',file=sys.stderr)
        raise SystemExit(1)


if __name__=='__main__':main()
