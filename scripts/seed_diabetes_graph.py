from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.research.corpus import Corpus
from backend.app.research.graph import DiabetesGraph
if __name__=='__main__':
    graph=DiabetesGraph()
    try:
        first=graph.ingest(Corpus());second=graph.ingest(Corpus());assert first==second
        path=Path('docs/validation/diabetes_expansion');path.mkdir(parents=True,exist_ok=True)
        (path/'graph_ingestion.json').write_text(json.dumps(first,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in first.items() if k!='assertions'},indent=2))
    finally:graph.store.close()
