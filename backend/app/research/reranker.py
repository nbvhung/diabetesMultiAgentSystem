"""Small multilingual cross encoder; local checksummed CPU inference, never request downloads."""
from pathlib import Path
from threading import RLock
import hashlib,json
import numpy as np
from .config import ROOT,research_settings
from .semantic import SemanticUnavailable

MODEL_ID='cross-encoder/mmarco-mMiniLMv2-L12-H384-v1'


class Reranker:
    def __init__(self,path=None):self.path=Path(path or research_settings.diabetes_reranker_dir);self.loaded=False;self.lock=RLock()
    def load(self):
        with self.lock:
            if self.loaded:return
            try:
                meta=json.loads((self.path/'manifest.json').read_text(encoding='utf-8'))
                if meta['model_id']!=MODEL_ID:raise ValueError('Wrong reranker')
                for name,digest in meta['files'].items():
                    path=(self.path/name).resolve()
                    if not path.is_relative_to(self.path.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Reranker checksum mismatch')
                from sentence_transformers import CrossEncoder
                import torch
                torch.set_num_threads(2)
                self.model=CrossEncoder(str(self.path/'model'),device='cpu',max_length=256,local_files_only=True,trust_remote_code=False,activation_fn=torch.nn.Sigmoid())
                self.meta=meta;self.loaded=True
            except Exception:raise SemanticUnavailable('RERANKER_UNAVAILABLE') from None
    def score(self,query,passages):
        self.load()
        with self.lock:return np.asarray(self.model.predict([(query,p) for p in passages],batch_size=8,show_progress_bar=False),dtype='float32').ravel()


def prepare_reranker(download=False):
    from huggingface_hub import snapshot_download
    from sentence_transformers import CrossEncoder
    target=research_settings.diabetes_reranker_dir;target.mkdir(parents=True,exist_ok=True)
    cache=Path(snapshot_download(MODEL_ID,cache_dir=ROOT/'.tools/hf-cache',local_files_only=not download,allow_patterns=['*.json','*.txt','*.safetensors','*.model']))
    model=CrossEncoder(str(cache),device='cpu',local_files_only=True,trust_remote_code=False)
    model.save(str(target/'model'),safe_serialization=True)
    meta={'model_id':MODEL_ID,'source_revision':cache.name,'device':'cpu','license':'Apache-2.0, upstream model card','files':{p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (target/'model').rglob('*') if p.is_file()}}
    (target/'manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta
