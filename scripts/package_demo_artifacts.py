"""Package trusted local demo artifacts without env files, raw patients or DB dumps.

The archive is a local handoff, never published automatically. Pima-derived
checkpoints have unresolved redistribution rights; review before sharing.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--include-retrieval',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'.tools/exports/diabetes-demo-artifacts.zip');args=parser.parse_args()
    folders=['artifacts/models','artifacts/policies','data/knowledge','experiments/results','experiments/figures']
    if args.include_retrieval:folders.append('artifacts/embeddings')
    paths=[p for folder in folders for p in (ROOT/folder).rglob('*') if p.is_file() and p.name!='.gitkeep']
    records={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest={'timestamp':datetime.now(timezone.utc).isoformat(),'files':records,'retrieval_weights_included':args.include_retrieval,'raw_pima_included':False,'secrets_included':False,'note':'Local trusted handoff only. Review Pima-derived artifact redistribution rights. Retrieval weights can be prepared separately from recorded upstream revisions.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'x',compression=zipfile.ZIP_STORED if args.include_retrieval else zipfile.ZIP_DEFLATED) as archive:
        for path in paths:archive.write(path,path.relative_to(ROOT).as_posix())
        archive.writestr('demo_artifacts_manifest.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(args.output) as archive:
        assert all(hashlib.sha256(archive.read(name)).hexdigest()==digest for name,digest in records.items())
    summary={'path':str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else args.output.name,'files':len(paths),'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'retrieval_weights_included':args.include_retrieval}
    (args.output.with_suffix('.manifest.json')).write_text(json.dumps({**manifest,**summary},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
