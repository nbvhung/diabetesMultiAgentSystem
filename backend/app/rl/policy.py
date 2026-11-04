"""Validated numeric NPZ/JSON, no pickle or request-time training."""
from pathlib import Path
from threading import RLock
from typing import Literal
import hashlib,json,zipfile
import numpy as np
from pydantic import BaseModel,ConfigDict,Field
from backend.app.rl.mdp import *
DEFAULT_PATH=Path(__file__).resolve().parents[3]/'artifacts/policies/education-q-1.1'

class Config(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    episodes_per_seed:int=Field(gt=0)
    alpha:float=Field(gt=0,le=1)
    gamma:float=Field(ge=0,le=1)
    epsilon_initial:float=Field(ge=0,le=1)
    epsilon_decay:float=Field(gt=0,le=1)
    epsilon_min:float=Field(ge=0,le=1)
    horizon:Literal[6]

class Manifest(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    format_version:Literal['1.1']
    evaluation_policy:Literal['serving-policy-fallback-v1']
    policy_version:Literal['education-q-1.1']
    reward_version:Literal['education-reward-1.0']
    state_fields:list[str]
    state_values:dict[str,list[str]]
    state_shape:list[int]
    actions:list[str]
    training_config:Config
    training_seeds:list[int]
    selected_seed:int
    validation_seeds:list[int]
    evaluation_seeds:list[int]
    q_table_sha256:str=Field(pattern='^[a-f0-9]{64}$')
    evaluation_metrics:dict
    environment:dict[str,str]
    scope:str

class PolicyUnavailable(Exception):pass

class PolicyService:
    def __init__(self,path=DEFAULT_PATH):
        self.path=Path(path);self._lock=RLock();self._loaded=False;self._failed=False
    def load(self):
        with self._lock:
            if self._failed:raise PolicyUnavailable('POLICY_UNAVAILABLE')
            if self._loaded:return
            try:
                if (self.path/'manifest.json').stat().st_size>1_000_000:raise ValueError('Manifest too large')
                meta=Manifest.model_validate_json((self.path/'manifest.json').read_text())
                if meta.state_values!=STATE_VALUES or meta.actions!=list(ACTIONS) or meta.state_fields!=list(STATE_FIELDS) or meta.state_shape!=list(SHAPE):raise ValueError('Encoder mismatch')
                if meta.selected_seed not in meta.training_seeds or set(meta.validation_seeds)&set(meta.evaluation_seeds):raise ValueError('Invalid experiment seeds')
                file=self.path/'q_table.npz'
                if hashlib.sha256(file.read_bytes()).hexdigest()!=meta.q_table_sha256:raise ValueError('Checksum mismatch')
                with zipfile.ZipFile(file) as archive:
                    if sum(i.file_size for i in archive.infolist())>10_000_000:raise ValueError('Expanded artifact too large')
                with np.load(file,allow_pickle=False) as data:
                    if set(data.files)!={'q','visits'}:raise ValueError('Unexpected table fields')
                    q=data['q'].copy();visits=data['visits'].copy()
                if q.shape!=(N_STATES,6) or q.dtype.kind!='f' or not np.isfinite(q).all():raise ValueError('Invalid Q table')
                if visits.shape!=(N_STATES,) or visits.dtype.kind not in 'iu' or (visits<0).any() or not np.any(visits):raise ValueError('Invalid visit counts')
                q.flags.writeable=False;visits.flags.writeable=False
                self.q=q;self.visits=visits;self.manifest=meta;self._loaded=True
            except Exception:
                self._failed=True;raise PolicyUnavailable('POLICY_UNAVAILABLE') from None
    def choose(self,state):
        try:row=encode(state)
        except (ValueError,TypeError):return ACTIONS[4],'fallback','INVALID_STATE','fallback-rule-1.0'
        try:self.load()
        except PolicyUnavailable:return ACTIONS[baseline(state)],'fallback','POLICY_UNAVAILABLE','fallback-rule-1.0'
        from backend.app.rl.selection import select_action
        action,source,reason=select_action(self.q,self.visits,state)
        version=self.manifest.policy_version if source=='policy' else 'fallback-rule-1.0'
        return ACTIONS[action],source,reason,version
