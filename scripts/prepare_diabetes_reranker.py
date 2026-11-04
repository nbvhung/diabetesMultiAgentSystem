from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.research.reranker import prepare_reranker
if __name__=='__main__':
    meta=prepare_reranker(download='--download' in sys.argv)
    print(json.dumps({k:v for k,v in meta.items() if k!='files'},indent=2))
