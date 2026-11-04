"""One serving decision implementation for validation, evaluation and runtime."""
from backend.app.rl.mdp import ACTIONS,encode,allowed_actions,baseline

def select_action(q,visits,state):
    row=encode(state)
    if not visits[row]:return baseline(state),'fallback','UNVISITED_STATE'
    choices=allowed_actions(state)
    return max(choices,key=lambda a:(q[row,a],-a)),'policy','TRAINED_Q_TABLE'
