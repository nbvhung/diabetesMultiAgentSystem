"""Synthetic simulator tests; no patient or clinical outcome assertions."""
import asyncio,json,shutil
from dataclasses import replace
from pathlib import Path
from uuid import uuid4
import numpy as np
import pytest
from backend.app.rl.mdp import *
from backend.app.rl.reward import reward
from backend.app.rl.learning import td_update,train
from backend.app.rl.policy import PolicyService,PolicyUnavailable,DEFAULT_PATH
from backend.app.mas.agents.rl_decision import RLDecisionAgent
from backend.app.mas.agents.safety import SafetyAgent
from backend.app.schemas.contracts import AgentName,PredictionResult
from backend.app.schemas.runtime import AgentMessage,RLTask,RunInput,AgentStatus,WorkflowStatus


def test_seeded_transition_and_reset_api():
    a,b=EducationEnv(),EducationEnv()
    initial=(1,0,1,2,0,6,6)
    assert a.reset(seed=123,options={'state':initial})==b.reset(seed=123,options={'state':initial})
    for action in [0,2,3,4,3,5]:
        x=a.step(action);y=b.step(action);assert x==y
        assert len(x)==5 and x[4]['simulated'] and isinstance(x[1],float)
        if x[2] or x[3]:break
    with pytest.raises(RuntimeError):a.step(0)

def test_mdp_restrictions_reward_and_horizon():
    env=EducationEnv();s,_=env.reset(seed=1,options={'state':(1,0,0,0,1,6,1)})
    new,r,t,tr,info=env.step(0)
    assert r==-20 and not t and tr and info['unsafe_attempt']==1
    assert allowed_actions(s)==(4,5)
    assert reward((1,1,1,2,0,0,6),0,(1,1,1,2,0,0,5),False,False,False)==pytest.approx(-.95)
    env.reset(seed=1,options={'state':(1,2,1,2,0,6,6)})
    assert env.step(3)[2] is True
    env.reset(seed=1,options={'state':(0,0,0,0,1,6,6)})
    assert env.step(5)[4]['completed'] is True

@pytest.mark.parametrize('action',[-1,6,99,'ADJUST_INSULIN',True])
def test_invalid_action_never_enters_environment(action):
    env=EducationEnv();env.reset(seed=1)
    with pytest.raises(ValueError):env.step(action)

def test_q_update_terminal_and_truncated_targets():
    q=np.zeros((2,6));q[1]=100
    assert td_update(q,0,2,3,1,True,False,.5,.9)==3
    assert q[0,2]==1.5
    q[0,2]=0
    assert td_update(q,0,2,3,1,False,True,.5,.9)==3
    q[0,2]=0
    assert td_update(q,0,2,3,1,False,False,.5,.9)==93
    assert q[0,2]==46.5

def test_small_training_reproducible_and_actually_updates_q():
    q,v,h=train(9,episodes=100);q2,v2,h2=train(9,episodes=100)
    np.testing.assert_array_equal(q,q2);np.testing.assert_array_equal(v,v2)
    assert h==h2 and np.count_nonzero(q)>0

@pytest.mark.parametrize('state',[(3,0,0,0,0,6,6),(0,0,0,0,0,6),('invalid',0,0,0,0,6,6)])
def test_invalid_state_fallback(state):
    action,source,reason,version=PolicyService().choose(state)
    assert action=='REQUEST_CLARIFICATION' and source=='fallback' and reason=='INVALID_STATE'
    assert version=='fallback-rule-1.0'

def test_trained_artifact_loaded_readonly_and_visited_policy_used():
    service=PolicyService();service.load()
    assert np.count_nonzero(service.q)>0 and service.manifest.policy_version=='education-q-1.1'
    states=np.flatnonzero(service.visits>0)
    state=tuple(int(x) for x in np.unravel_index(int(states[0]),SHAPE))
    action,source,reason,version=service.choose(state)
    assert action in ACTIONS and source=='policy' and version=='education-q-1.1'
    with pytest.raises(ValueError):service.q[0,0]=1
    assert service.choose(state)==service.choose(state)
    unseen=int(np.flatnonzero(service.visits==0)[0]);state=tuple(int(x) for x in np.unravel_index(unseen,SHAPE))
    assert service.choose(state)[1:3]==('fallback','UNVISITED_STATE')

@pytest.mark.parametrize('mode',['missing','corrupt','actions','shape','reward_version'])
def test_missing_or_invalid_artifact_falls_back_safely(tmp_path,mode):
    folder=tmp_path/'policy'
    if mode!='missing':
        shutil.copytree(DEFAULT_PATH,folder)
        if mode=='corrupt':(folder/'q_table.npz').write_bytes(b'corrupt')
        else:
            meta=json.loads((folder/'manifest.json').read_text())
            if mode=='actions':meta['actions'][0]='ADJUST_INSULIN'
            elif mode=='shape':meta['state_shape'][0]=999
            else:meta['reward_version']='unrecognized'
            (folder/'manifest.json').write_text(json.dumps(meta))
    service=PolicyService(folder)
    with pytest.raises(PolicyUnavailable):service.load()
    action,source,reason,version=service.choose((0,1,1,0,0,6,6))
    assert action in ACTIONS and source=='fallback' and reason=='POLICY_UNAVAILABLE'
    assert version=='fallback-rule-1.0'

def test_agent_and_concurrent_requests_do_not_learn_or_share_state():
    service=PolicyService();service.load();q=service.q.copy();agent=RLDecisionAgent(service)
    async def scenario():
        return await asyncio.gather(*(agent.execute(AgentMessage(run_id=uuid4(),recipient=AgentName.rl,payload=RLTask())) for _ in range(20)))
    results=asyncio.run(scenario())
    assert all(r.output.action in ACTIONS and r.output.decision_source=='policy' for r in results)
    results[0].output.state['mutation']='synthetic-test'
    assert all('mutation' not in r.output.state for r in results[1:])
    np.testing.assert_array_equal(q,service.q)

def test_real_rl_coordinator_call_trace_and_safety_veto():
    from backend.app.mas.registry import AgentRegistry
    from backend.app.mas.agents.runtime import PredictionAgent,KnowledgeAgent,EducationAgent
    from backend.app.mas.coordinator import Coordinator
    from backend.app.mas.agents.knowledge import EducationAgent as GroundedEducation
    registry=AgentRegistry()
    for agent in [PredictionAgent(),KnowledgeAgent(),RLDecisionAgent(),GroundedEducation(),SafetyAgent()]:registry.register(agent)
    result=asyncio.run(Coordinator(registry).run(RunInput(question='What is diabetes?')))
    decision=result.agent_results[AgentName.rl].output
    assert result.agent_results[AgentName.rl].status==AgentStatus.COMPLETED
    assert decision.policy_version=='education-q-1.1' and decision.action in ACTIONS
    event=next(e for e in result.agent_trace if e.agent_id==AgentName.rl and e.policy_version)
    assert (event.policy_version,event.action,event.decision_source)==(decision.policy_version,decision.action,decision.decision_source)
    blocked=asyncio.run(Coordinator(registry).run(RunInput(question='Prescribe insulin')))
    assert blocked.status==WorkflowStatus.BLOCKED and blocked.agent_results[AgentName.rl].status==AgentStatus.SKIPPED

def test_notebook_executed_and_simulator_seed_partitions():
    import nbformat
    nb=nbformat.read(DEFAULT_PATH.parents[2]/'notebooks/04_rl_q_learning_training.ipynb',as_version=4)
    cells=[c for c in nb.cells if c.cell_type=='code']
    assert cells and all(c.execution_count is not None for c in cells)
    assert not any(o.output_type=='error' for c in cells for o in c.outputs)
    meta=json.loads((DEFAULT_PATH/'manifest.json').read_text())
    train_seeds={seed*1_000_000+i for seed in meta['training_seeds'] for i in range(meta['training_config']['episodes_per_seed'])}
    assert not train_seeds&set(meta['validation_seeds']) and not train_seeds&set(meta['evaluation_seeds'])
    assert not set(meta['validation_seeds'])&set(meta['evaluation_seeds'])


def test_selected_seed_metadata_matches_validation_selection():
    report=json.loads((DEFAULT_PATH.parents[2]/'experiments/results/phase06/evaluation.json').read_text())
    manifest=json.loads((DEFAULT_PATH/'manifest.json').read_text())
    chosen=max(report['training_runs'],key=lambda seed:(report['training_runs'][seed]['validation']['average_episode_reward'],-int(seed)))
    assert manifest['selected_seed']==report['selected_seed']==int(chosen)
