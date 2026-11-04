"""Load once per app; never fit, retrain, or choose alternate versions."""
import json, time
from pathlib import Path
from threading import RLock
import joblib
import numpy as np
import pandas as pd
import torch
from backend.app.ml.pipeline import MLP, FEATURES, ZERO_MISSING, ART, VERSION, sha
from backend.app.schemas.contracts import AssessmentInput
from backend.app.schemas.prediction import PredictionResult

class ModelUnavailable(Exception): pass

class ModelService:
    def __init__(self, artifact_dir=ART, expected_version=VERSION, device='cpu'):
        self.path=Path(artifact_dir).resolve(); self.version=expected_version; self.device=device
        self._lock=RLock(); self._loaded=False; self._error=None

    def load(self):
        with self._lock:
            if self._error: raise ModelUnavailable(self._error)
            if self._loaded: return
            try:
                manifest=json.loads((self.path/'manifest.json').read_text())
                serving=json.loads((self.path/'serving.json').read_text())
                if manifest['model_version']!=self.version or serving['model_version']!=self.version:
                    raise ValueError('MODEL_VERSION_MISMATCH')
                if sha(self.path/'manifest.json')!=serving['manifest_sha256']: raise ValueError('MANIFEST_CHECKSUM_MISMATCH')
                required={'checkpoint.pt','preprocessing.joblib','preprocessing_config.json','training_config.json'}
                if set(manifest['sha256'])!=required: raise ValueError('MANIFEST_SCHEMA_MISMATCH')
                for name,digest in manifest['sha256'].items():
                    if sha(self.path/name)!=digest: raise ValueError('ARTIFACT_CHECKSUM_MISMATCH')
                config=json.loads((self.path/'preprocessing_config.json').read_text())
                checkpoint=torch.load(self.path/'checkpoint.pt',map_location='cpu',weights_only=True)
                if checkpoint['model_version']!=self.version: raise ValueError('CHECKPOINT_VERSION_MISMATCH')
                if checkpoint['input_features']!=FEATURES or config['features']!=FEATURES or serving['features']!=FEATURES or config['zero_as_missing']!=ZERO_MISSING:
                    raise ValueError('FEATURE_SCHEMA_MISMATCH')
                if self.device not in ('cpu','cuda') or (self.device=='cuda' and not torch.cuda.is_available()): raise ValueError('DEVICE_UNAVAILABLE')
                model=MLP(); model.load_state_dict(checkpoint['state_dict']); model.to(self.device).eval()
                pipe=joblib.load(self.path/'preprocessing.joblib')
                if list(pipe.feature_names_in_)!=FEATURES: raise ValueError('PREPROCESSING_FEATURE_MISMATCH')
                self.model=model; self.pipe=pipe; self.bounds=serving['training_bounds']; self.digest=manifest['sha256']['checkpoint.pt']
                self.preprocessing_version='sha256:'+manifest['sha256']['preprocessing.joblib']
                self._loaded=True
            except Exception as exc:
                self._error=str(exc) if isinstance(exc,ValueError) else 'MODEL_ARTIFACT_UNAVAILABLE'
                raise ModelUnavailable(self._error) from None

    def predict(self, assessment: AssessmentInput):
        self.load()
        checked=AssessmentInput.model_validate(assessment.model_dump(),strict=True)
        start=time.perf_counter(); warnings=[]
        row={c:getattr(checked,c) for c in FEATURES}
        for c,v in row.items():
            lo,hi=self.bounds[c]
            if v<lo or v>hi: warnings.append('OUTSIDE_TRAINING_RANGE:'+c)
            if c in ZERO_MISSING and v==0: warnings.append('ZERO_TREATED_AS_MISSING:'+c)
        frame=pd.DataFrame([row],columns=FEATURES).replace({c:{0:np.nan} for c in ZERO_MISSING})
        with self._lock, torch.inference_mode():
            transformed=self.pipe.transform(frame).astype('float32')
            score=float(torch.sigmoid(self.model(torch.from_numpy(transformed).to(self.device))).cpu().item())
        return PredictionResult(model_id='pima-mlp',model_version=self.version,preprocessing_version=self.preprocessing_version,
            predicted_class=int(score>=0.5),score=score,inference_latency_ms=(time.perf_counter()-start)*1000,
            warnings=warnings,limitations=['Uncalibrated model score, not clinical disease probability.','Research on a restricted historical female Pima cohort; not a diagnosis.','Threshold 0.5; missing-zero transformation matches training.'])
