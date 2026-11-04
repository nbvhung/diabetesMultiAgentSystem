"""E4: exported serving Q-policy vs frozen rule policy on paired held-out seeds."""
from phase07_common import *
import statistics
from backend.app.rl.policy import PolicyService
from backend.app.rl.experiments import evaluate, TEST_SEEDS


def main():
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    service=PolicyService();service.load()
    reports={'q_learning':evaluate(service.q,TEST_SEEDS,decision_fn=service.choose),'rule_based':evaluate(None,TEST_SEEDS)}
    assert reports['q_learning']==evaluate(service.q,TEST_SEEDS,visits=service.visits),'Serving evaluation parity failed'
    keys=['average_episode_reward','completion_rate','reward_variance_across_scenarios','unsafe_action_attempts','mean_episode_length','fallback_decisions']
    summary=[{'policy':name,**{key:report[key] for key in keys}} for name,report in reports.items()]
    rows=[{'policy':name,**episode} for name,report in reports.items() for episode in report['episodes']]
    # The learning curve is real prior notebook output, checksummed as an input, never regenerated from made-up samples.
    history=pd.read_csv(RES/'phase06/training_history.csv')
    FIG.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for seed,group in history.groupby('seed'):
        axes[0].plot(group.episode,group.reward.rolling(200,min_periods=1).mean(),label=str(seed))
    axes[0].set_title('Actual Phase 06 training history');axes[0].set_xlabel('Episode');axes[0].set_ylabel('Simulator reward (rolling 200)');axes[0].legend(title='Training seed')
    axes[1].bar([r['policy'] for r in summary],[r['average_episode_reward'] for r in summary],color=['#3e8065','#b1c6a0'])
    axes[1].set_title('Paired held-out serving policy reward');fig.tight_layout();fig.savefig(FIG/'rl.png',dpi=150);plt.close(fig)
    save('rl',summary,rows,'SYNTHETIC educational simulator only; not patient health or measured learning outcomes.',datasets=['artifacts/policies/education-q-1.1/manifest.json','artifacts/policies/education-q-1.1/q_table.npz','experiments/results/phase06/training_history.csv'],config={'policy_version':service.manifest.policy_version,'evaluation_seeds':list(TEST_SEEDS),'selected_training_seed':service.manifest.selected_seed,'selection':'pre-existing Phase 06 validation selection; no tuning in Phase 07','parity_verified':True,'unsafe_action_attempts':'attempts under restricted simulator state before mask; serving policy evaluated with actual fallback'},seed=list(TEST_SEEDS),extra={'paired_mean_reward_difference':statistics.mean(a['reward']-b['reward'] for a,b in zip(reports['q_learning']['episodes'],reports['rule_based']['episodes']))})

if __name__=='__main__':main()
