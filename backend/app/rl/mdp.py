"""Synthetic educational interaction model. No health outcomes or medical actions."""
import numpy as np
ACTIONS=('EXPLAIN_PREDICTION_LIMITATIONS','PROVIDE_GENERAL_EDUCATION','SHOW_EVIDENCE','ASK_COMPREHENSION_QUESTION','REQUEST_CLARIFICATION','SUGGEST_CLINICIAN_DISCUSSION')
STATE_FIELDS=('prediction_band','knowledge','engagement','evidence','safety','previous_action','remaining')
SHAPE=(3,3,3,3,2,7,7)
N_STATES=int(np.prod(SHAPE))
REWARD_VERSION='education-reward-1.0'
STATE_VALUES=dict(zip(STATE_FIELDS,[['unavailable','lower-score','higher-score'],['low','medium','high'],['low','medium','high'],['none','partial','sufficient'],['normal','restricted'],list(ACTIONS)+['NONE'],[str(i) for i in range(7)]]))

def encode(state):
    if len(state)!=len(SHAPE) or any(type(x) not in (int,np.int64,np.int32) or not 0<=x<n for x,n in zip(state,SHAPE)):
        raise ValueError('OUT_OF_ENCODER_RANGE')
    return int(np.ravel_multi_index(tuple(state),SHAPE))

def allowed_actions(s):
    if s[4]==1:return (4,5)
    return tuple(a for a in range(6) if not(a in (1,2) and s[3]==0))

def baseline(s):
    if s[4]:return 5
    if not s[3]:return 4
    if s[1]>=2 and s[2]>=1:return 3
    if s[2]==0:return 3
    if s[0] and s[5]!=0 and s[1]==0:return 0
    return 2 if s[3]==2 and s[5]!=2 else 1

class EducationEnv:
    def reset(self,seed=None,options=None):
        self.rng=np.random.default_rng(seed)
        initial=options.get('state') if options else None
        self.state=tuple(initial) if initial is not None else tuple(int(self.rng.integers(n)) for n in SHAPE[:5])+(6,6)
        encode(self.state)
        if self.state[-1]==0:raise ValueError('Reset requires positive remaining budget')
        self.done=False
        return self.state,{'simulated':True,'reward_version':REWARD_VERSION}

    def step(self,action):
        from backend.app.rl.reward import reward
        if self.done:raise RuntimeError('Reset after terminal step')
        if type(action) not in (int,np.int64,np.int32) or not 0<=action<6:raise ValueError('Invalid educational action')
        s=self.state;p,k,e,v,safety,last,left=s
        unsafe=safety==1 and action not in (4,5)
        unsupported=(action in (1,2) and v==0) or (action==0 and p==0)
        completed=False
        if not unsafe and not unsupported:
            if action==0:k=min(2,k+int(self.rng.random()<0.8))
            elif action in (1,2):
                k=min(2,k+int(self.rng.random()<(0.8 if action==2 else 0.65)))
                e=min(2,e+int(self.rng.random()<0.45))
            elif action==3:
                completed=k>=2 and e>=1 and v>0
                e=min(2,e+int(self.rng.random()<0.75))
            elif action==4:
                v=min(2,v+int(self.rng.random()<0.7));e=min(2,e+int(self.rng.random()<0.5))
            elif action==5:completed=safety==1
        new=(p,k,e,v,safety,int(action),left-1)
        r=reward(s,int(action),new,unsafe,unsupported,completed)
        terminated=bool(completed or action==5 and not unsafe)
        truncated=bool(not terminated and left-1==0)
        self.state=new;self.done=terminated or truncated
        return new,r,terminated,truncated,{'simulated':True,'completed':completed,'unsafe_attempt':int(unsafe),'unsupported':int(unsupported),'reward_version':REWARD_VERSION}
