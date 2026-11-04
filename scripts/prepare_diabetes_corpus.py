"""Explicit fetch/prepare only; runtime never downloads knowledge."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.research.corpus import prepare_corpus
if __name__=='__main__':
    report=prepare_corpus(fetch='--fetch' in sys.argv)
    print(json.dumps({k:v for k,v in report.items() if k!='sources'},indent=2))
