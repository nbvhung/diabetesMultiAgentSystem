from pathlib import Path
import hashlib,json,platform,statistics
import numpy as np
from backend.app.rl.mdp import *
from backend.app.rl.learning import train
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT/'artifacts/policies/education-q-1.1'
RES=ROOT/'experiments/results/phase06'
FIG=ROOT/'experiments/figures/phase06'
TRAIN_SEEDS=(11,29,47)
VALIDATION_SEEDS=tuple(range(200000,200100))
TEST_SEEDS=tuple(range(100000,100300))

def evaluate(q,seeds,mask=True,visits=None,decision_fn=None):
    from backend.app.rl.selection import select_action
    if q is not None and mask and visits is None and decision_fn is None:
        raise ValueError('Serving evaluation requires visit counts')
    rows=[];counts=np.zeros(6,dtype=int);fallback_count=0
    for seed in seeds:
        env=EducationEnv();state,_=env.reset(seed=seed);total=0.;unsafe=0;length=0;actions=[];sources=[]
        while True:
            if decision_fn is not None:
                action_name,source,reason,version=decision_fn(state);action=ACTIONS.index(action_name)
            elif q is None:action=baseline(state);source='baseline'
            elif mask:action,source,reason=select_action(q,visits,state)
            else:action=max(range(6),key=lambda a:(q[encode(state),a],-a));source='raw_q_diagnostic'
            if source=='fallback':fallback_count+=1
            counts[action]+=1;actions.append(int(action));sources.append(source)
            state,r,t,tr,info=env.step(int(action));total+=r;unsafe+=info['unsafe_attempt'];length+=1
            if t or tr:break
        rows.append({'simulator_seed':seed,'reward':total,'completed':int(info['completed']),'unsafe_attempts':unsafe,'length':length,'actions':actions,'decision_sources':sources})
    return {'average_episode_reward':statistics.mean(r['reward'] for r in rows),'completion_rate':statistics.mean(r['completed'] for r in rows),'unsafe_action_attempts':sum(r['unsafe_attempts'] for r in rows),'mean_episode_length':statistics.mean(r['length'] for r in rows),'reward_variance_across_scenarios':statistics.pvariance(r['reward'] for r in rows),'fallback_decisions':fallback_count,'action_counts':counts.tolist(),'episodes':rows}

def run_experiments():
    import pandas as pd
    import matplotlib.pyplot as plt
    import importlib.metadata as metadata
    for p in (ART,RES,FIG):p.mkdir(parents=True,exist_ok=True)
    candidates=[];histories=[];metrics={}
    for seed in TRAIN_SEEDS:
        q,visits,history=train(seed);histories.extend(history)
        validation=evaluate(q,VALIDATION_SEEDS,visits=visits)
        metrics[str(seed)]={'validation':validation,'held_out_serving':evaluate(q,TEST_SEEDS,visits=visits),'held_out_unmasked':evaluate(q,TEST_SEEDS,False)}
        candidates.append((validation['average_episode_reward'],seed,q,visits))
    selected=max(candidates,key=lambda x:(x[0],-x[1]));_,seed,q,visits=selected
    reference=evaluate(None,TEST_SEEDS)
    report={'scope':'SYNTHETIC educational simulator only, not clinical/health outcomes','selected_seed':seed,'selection':'highest validation serving-policy reward including fallback; held-out seeds not used for selection','training_runs':metrics,'baseline':reference,'aggregate':{}}
    for mode in ['held_out_serving','held_out_unmasked']:
        values=[metrics[str(s)][mode]['average_episode_reward'] for s in TRAIN_SEEDS]
        report['aggregate'][mode]={'reward_mean':statistics.mean(values),'reward_variance_across_training_seeds':statistics.pvariance(values),'completion_mean':statistics.mean(metrics[str(s)][mode]['completion_rate'] for s in TRAIN_SEEDS),'unsafe_attempts_total':sum(metrics[str(s)][mode]['unsafe_action_attempts'] for s in TRAIN_SEEDS),'episode_length_mean':statistics.mean(metrics[str(s)][mode]['mean_episode_length'] for s in TRAIN_SEEDS)}
    report['aggregate']['baseline']={'reward_mean':reference['average_episode_reward'],'reward_variance_across_training_seeds':0.0,'completion_mean':reference['completion_rate'],'unsafe_attempts_total':reference['unsafe_action_attempts'],'episode_length_mean':reference['mean_episode_length']}
    (RES/'evaluation.json').write_text(json.dumps(report,indent=2))
    frame=pd.DataFrame(histories);frame.to_csv(RES/'training_history.csv',index=False)
    for seed,g in frame.groupby('seed'):plt.plot(g.episode,g.reward.rolling(200,min_periods=1).mean(),label=str(seed))
    plt.legend(title='Training seed');plt.xlabel('Episode');plt.ylabel('Synthetic reward, rolling 200');plt.tight_layout();plt.savefig(FIG/'reward_curves.png');plt.show();plt.close()
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for seed,g in frame.groupby('seed'):axes[0].plot(g.episode,g.completed.rolling(200,min_periods=1).mean(),label=str(seed))
    axes[0].set_title('Simulated task completion');axes[0].legend()
    axes[1].bar(range(6),metrics[str(selected[1])]['held_out_serving']['action_counts']);axes[1].set_title('Held-out selected policy action counts');axes[1].set_xticks(range(6));fig.tight_layout();fig.savefig(FIG/'success_actions.png');plt.show();plt.close()
    visited=np.flatnonzero(visits>0)
    plt.figure(figsize=(9,5));plt.imshow(q[visited[:100]],aspect='auto',cmap='coolwarm');plt.colorbar(label='Learned Q');plt.xlabel('Action index');plt.ylabel('First 100 visited state IDs');plt.tight_layout();plt.savefig(FIG/'q_table.png');plt.show();plt.close()
    np.savez_compressed(ART/'q_table.npz',q=q,visits=visits)
    digest=hashlib.sha256((ART/'q_table.npz').read_bytes()).hexdigest()
    manifest={'format_version':'1.1','evaluation_policy':'serving-policy-fallback-v1','policy_version':'education-q-1.1','reward_version':REWARD_VERSION,'state_fields':list(STATE_FIELDS),'state_values':STATE_VALUES,'state_shape':list(SHAPE),'actions':list(ACTIONS),'training_config':{'episodes_per_seed':8000,'alpha':.15,'gamma':.95,'epsilon_initial':1.0,'epsilon_decay':.9994,'epsilon_min':.05,'horizon':6},'training_seeds':list(TRAIN_SEEDS),'selected_seed':selected[1],'validation_seeds':list(VALIDATION_SEEDS),'evaluation_seeds':list(TEST_SEEDS),'q_table_sha256':digest,'evaluation_metrics':report['aggregate'],'environment':{'python':platform.python_version(),'numpy':np.__version__,'nbconvert':metadata.version('nbconvert')},'scope':report['scope']}
    (ART/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'selected_seed':selected[1],'aggregate':report['aggregate']},indent=2))
    return report,frame,q
