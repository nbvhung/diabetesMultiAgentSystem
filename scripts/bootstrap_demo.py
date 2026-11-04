"""Idempotent initialization of the current schema and source-bound diabetes graph."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def initialize():
    from alembic.config import Config
    from alembic import command
    from backend.app.research.corpus import Corpus
    from backend.app.research.graph import DiabetesGraph
    from backend.app.ml.serving import ModelService
    from backend.app.rl.policy import PolicyService
    from backend.app.research.semantic import SemanticEncoder
    from backend.app.research.reranker import Reranker
    command.upgrade(Config('alembic.ini'),'head')
    model=ModelService();model.load()
    policy=PolicyService();policy.load()
    encoder=SemanticEncoder();encoder.load()
    reranker=Reranker();reranker.load()
    graph=DiabetesGraph()
    try:
        seeded=graph.ingest(Corpus())
        result={'migration':'0002_phase03','model':'loaded','policy':'loaded','encoder':'loaded','reranker':'loaded','chunks':seeded['chunks'],'sources':seeded['sources'],'assertions':len(seeded['assertions'])}
        assert result['chunks']>0 and result['sources']>0
        return result
    finally:graph.store.close()

if __name__=='__main__':print(json.dumps(initialize(),indent=2))
