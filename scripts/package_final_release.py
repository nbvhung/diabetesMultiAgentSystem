"""Export source and a separate trusted artifact handoff; never publish secrets."""
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile
from datetime import datetime,timezone
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def package(destination):
    destination.mkdir(parents=True,exist_ok=True)
    raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
    files={ROOT/name for name in raw.decode().split('\0') if name}
    files.update((ROOT/'docs/report/figures').glob('*.png'))
    files={p for p in files if p.is_file()}
    values=[]
    for env in ['.env','.env.compose','.env.demo','.env.phase08-test']:
        values.extend(v for k,v in dotenv_values(ROOT/env).items() if v and len(v)>=12 and any(part in k for part in ['PASSWORD','KEY','DATABASE_URL']))
    for path in files:
        if not path.resolve().is_relative_to(ROOT):raise RuntimeError('Archive path outside project')
        if path.name.startswith('.env') and path.name!='.env.example':raise RuntimeError('Environment file rejected')
        if path.stat().st_size>5*1024*1024:raise RuntimeError('Unexpected heavy source file: '+path.name)
        if path.suffix not in ('.png','.woff2','.woff'):
            text=path.read_text(encoding='utf-8',errors='replace')
            if any(value in text for value in values):raise RuntimeError('Configured secret found; archive not created')
    archive=destination/'source.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as output:
        for path in sorted(files):output.write(path,path.relative_to(ROOT).as_posix())
    artifacts=destination/'artifacts.zip'
    subprocess.run(['python','scripts/package_demo_artifacts.py','--include-retrieval','--output',str(artifacts)],cwd=ROOT,check=True)
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'source_files':len(files),'source_zip':{'bytes':archive.stat().st_size,'sha256':digest(archive)},'artifact_zip':{'bytes':artifacts.stat().st_size,'sha256':digest(artifacts)},'secrets_included':False,'raw_pima_included':False,'deployment_scope':'native demo; Docker runtime not verified','instructions':'Extract source.zip and artifacts.zip into the same new folder; configure .env; follow docs/installation.md then python scripts/start_final_demo.py start. Requires installed dependencies and services; not a standalone executable.'}
    (destination/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'.tools/exports/final_native_release');args=parser.parse_args();package(args.output)
