"""Ingest only accessed NIDDK text; reruns MERGE deterministic content IDs."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.knowledge.store import GraphStore,documents,DATA
if __name__=='__main__':
 chunks=documents(fetch='--fetch' in sys.argv)
 store=GraphStore()
 try:
  before=store.summary(); first=store.ingest(chunks); second=store.ingest(chunks)
  assert first==second,'Ingestion is not idempotent'
  report={'before':before,'after':first,'second_run':second,'idempotent':True,'chunks':[ {k:v for k,v in c.items() if k!='embedding'} for c in chunks]}
  target=Path(__file__).resolve().parents[1]/'docs/validation/phase04';target.mkdir(parents=True,exist_ok=True)
  (target/'ingestion.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(first)
 finally: store.close()
