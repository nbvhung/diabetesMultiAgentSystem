"""CPU multilingual sentence encoder with explicit offline, checksummed preparation."""
from pathlib import Path
from threading import RLock
import hashlib,json
import numpy as np
from .config import research_settings

MODEL_ID='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'


class SemanticUnavailable(Exception):pass


class SemanticEncoder:
    def __init__(self,path=None):self.path=Path(path or research_settings.diabetes_semantic_dir);self._loaded=False;self.lock=RLock()
    def load(self):
        with self.lock:
            if self._loaded:return
            try:
                meta=json.loads((self.path/'manifest.json').read_text(encoding='utf-8'))
                if meta['model_id']!=MODEL_ID:raise ValueError('Encoder mismatch')
                for name,digest in meta['files'].items():
                    path=(self.path/name).resolve()
                    if not path.is_relative_to(self.path.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Encoder checksum mismatch')
                from sentence_transformers import SentenceTransformer
                import torch
                torch.set_num_threads(2)
                self.model=SentenceTransformer(str(self.path/'model'),device='cpu',local_files_only=True,trust_remote_code=False)
                self.meta=meta;self._loaded=True
            except Exception:raise SemanticUnavailable('SEMANTIC_MODEL_UNAVAILABLE') from None
    def encode(self,texts):
        self.load()
        with self.lock:return np.asarray(self.model.encode(texts,batch_size=16,normalize_embeddings=True,show_progress_bar=False),dtype='float32')


def prepare_encoder(*,download=False):
    from huggingface_hub import snapshot_download
    from sentence_transformers import SentenceTransformer
    import shutil
    target=research_settings.diabetes_semantic_dir;target.mkdir(parents=True,exist_ok=True)
    cached=Path(snapshot_download(MODEL_ID,local_files_only=not download,allow_patterns=['*.json','*.txt','*.safetensors','*.model','1_Pooling/*']))
    model=SentenceTransformer(str(cached),device='cpu',local_files_only=True,trust_remote_code=False)
    model.save(str(target/'model'),safe_serialization=True)
    files={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (target/'model').rglob('*') if p.is_file()}
    meta={'model_id':MODEL_ID,'source_revision':cached.name,'dimensions':model.get_sentence_embedding_dimension(),'device':'cpu','license':'Apache-2.0, upstream model card','files':files}
    (target/'manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta
