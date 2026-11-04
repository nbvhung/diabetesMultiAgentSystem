import numpy as np
from backend.app.rl.mdp import EducationEnv,N_STATES,encode

def td_update(q,s,a,r,next_s,terminated,truncated,alpha,gamma):
    target=r if terminated or truncated else r+gamma*float(q[next_s].max())
    q[s,a]+=alpha*(target-q[s,a])
    return float(target)

def train(seed,episodes=8000,alpha=.15,gamma=.95):
    rng=np.random.default_rng(seed)
    q=np.zeros((N_STATES,6),dtype=np.float64);visits=np.zeros(N_STATES,dtype=np.int64)
    env=EducationEnv(); history=[]
    for episode in range(episodes):
        state,_=env.reset(seed=seed*1_000_000+episode)
        epsilon=max(.05,1.0*(.9994**episode));total=0.;length=0;unsafe=0
        while True:
            row=encode(state);visits[row]+=1
            # Training explores all six educational actions, including unsupported contexts.
            action=int(rng.integers(6)) if rng.random()<epsilon else int(np.argmax(q[row]))
            new,r,term,trunc,info=env.step(action)
            td_update(q,row,action,r,encode(new),term,trunc,alpha,gamma)
            total+=r;length+=1;unsafe+=info['unsafe_attempt'];state=new
            if term or trunc:break
        history.append({'seed':seed,'episode':episode,'reward':total,'length':length,'completed':int(info['completed']),'unsafe_attempts':unsafe,'epsilon':epsilon})
    return q,visits,history
