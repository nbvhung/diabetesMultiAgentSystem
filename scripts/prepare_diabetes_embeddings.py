from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.research.semantic import prepare_encoder,SemanticEncoder
from backend.app.research.corpus import Corpus
from backend.app.research.config import research_settings
import numpy as np

if __name__=='__main__':
    meta=prepare_encoder(download='--download' in sys.argv)
    corpus=Corpus();corpus.load();encoder=SemanticEncoder()
    vectors=encoder.encode([c['title']+' / '+c['section']+' / '+c['text'] for c in corpus.chunks])
    path=research_settings.diabetes_semantic_dir/'corpus_vectors.npz'
    np.savez_compressed(path,vectors=vectors,ids=np.asarray([c['id'] for c in corpus.chunks]))
    index={'corpus_sha256':corpus.manifest['chunks_sha256'],'encoder_manifest_sha256':hashlib.sha256((path.parent/'manifest.json').read_bytes()).hexdigest(),'vectors_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'shape':list(vectors.shape)}
    (path.parent/'corpus_index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
    print(json.dumps({'model_id':meta['model_id'],'revision':meta['source_revision'],'index':index},indent=2))
