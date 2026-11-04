"""Regression proofs for review H1/H2/M1/L1/L2, all adverse agents synthetic."""
import asyncio,json,re
from dataclasses import replace
from pathlib import Path
import pytest
from backend.app.rl.mdp import ACTIONS
from backend.app.rl.policy import PolicyService,DEFAULT_PATH
from backend.app.rl.experiments import evaluate,TEST_SEEDS
from backend.app.mas.registry import AgentRegistry
from backend.app.mas.coordinator import Coordinator
from backend.app.mas.agents.runtime import PredictionAgent,KnowledgeAgent,RLDecisionAgent as StubRL
from backend.app.mas.agents.knowledge import EducationAgent
from backend.app.mas.agents.safety import SafetyAgent
from backend.app.schemas.contracts import AgentName,RLDecision
from backend.app.schemas.runtime import AgentResult,AgentStatus,RunInput
from backend.app.rules.engine import Context,RuleEngine

@pytest.mark.parametrize('bad_action',['START_METFORMIN','ADJUST_MEDICATION','TAKE_5_MG_METFORMIN','UNSUPPORTED_ACTION',''])
def test_bad_rl_action_never_reaches_education_or_response(bad_action):
    class InvalidRL(StubRL):
        def __init__(self):
            super().__init__();self.definition=replace(self.definition,available=True,implementation='integrated')
        async def execute(self,message):
            return AgentResult(agent_id=AgentName.rl,status=AgentStatus.COMPLETED,implementation='integrated',output=RLDecision(state={'fixture':'SYNTHETIC_FAULTY_AGENT'},action=bad_action,policy_version='SYNTHETIC_TEST',decision_source='policy'))
    registry=AgentRegistry()
    for a in [PredictionAgent(),KnowledgeAgent(),InvalidRL(),EducationAgent(),SafetyAgent()]:registry.register(a)
    run=asyncio.run(Coordinator(registry).run(RunInput(question='What is diabetes?')))
    assert run.status.value=='BLOCKED'
    assert run.agent_results[AgentName.rl].output is None
    assert run.agent_results[AgentName.rl].errors==['RL_ACTION_NOT_ALLOWED']
    assert run.agent_results[AgentName.education].status==AgentStatus.SKIPPED
    assert 'W04_ACTION_NOT_ALLOWED' in run.safety_decisions[-1].rule_ids
    assert [d.stage for d in run.safety_decisions]==['input','output']
    if bad_action:assert bad_action not in run.model_dump_json()

@pytest.mark.parametrize('bad_action',['START_METFORMIN','ADJUST_MEDICATION','unknown','show_evidence'])
def test_independent_safety_rule_rejects_unknown_action(bad_action):
    decision=RuleEngine().evaluate(Context(stage='output',candidate='safe fixed text',abstention=True,action=bad_action))
    assert decision.decision=='BLOCK' and 'W04_ACTION_NOT_ALLOWED' in decision.rule_ids

def test_serving_and_evaluator_have_exact_full_trajectory_parity():
    service=PolicyService();service.load()
    deployed=evaluate(service.q,TEST_SEEDS,decision_fn=service.choose)
    shared=evaluate(service.q,TEST_SEEDS,visits=service.visits)
    assert deployed==shared
    assert shared['fallback_decisions']>0,'This regression must exercise unseen states'
    with pytest.raises(ValueError,match='visit counts'):evaluate(service.q,TEST_SEEDS)

@pytest.mark.parametrize('action',[ACTIONS[1],ACTIONS[2],ACTIONS[3]])
def test_render_override_is_explicit(action):
    from backend.app.rl.rendering import render_plan
    plan=render_plan(action,[])
    assert plan.proposed_action==action and plan.effective_action==ACTIONS[4]
    assert plan.override_reason=='NO_EVIDENCE_FOR_REQUESTED_ACTION'

def test_coordinator_persists_proposed_and_effective_actions():
    class ComprehensionRL(StubRL):
        def __init__(self):
            super().__init__();self.definition=replace(self.definition,available=True,implementation='integrated')
        async def execute(self,message):
            return AgentResult(agent_id=AgentName.rl,status=AgentStatus.COMPLETED,implementation='integrated',output=RLDecision(state={'fixture':'SYNTHETIC_ACTION_TEST'},action=ACTIONS[3],policy_version='SYNTHETIC_TEST',decision_source='policy'))
    registry=AgentRegistry()
    for a in [PredictionAgent(),KnowledgeAgent(),ComprehensionRL(),EducationAgent(),SafetyAgent()]:registry.register(a)
    run=asyncio.run(Coordinator(registry).run(RunInput(question='What is diabetes?')))
    output=run.agent_results[AgentName.education].output
    assert output.proposed_action==ACTIONS[3] and output.effective_action==ACTIONS[4]
    assert output.override_reason=='NO_EVIDENCE_FOR_REQUESTED_ACTION'
    for name in [AgentName.education,AgentName.rl]:
        event=next(e for e in run.agent_trace if e.agent_id==name and e.proposed_action)
        assert event.proposed_action==ACTIONS[3] and event.effective_action==ACTIONS[4]
        assert event.action_override_reason==output.override_reason

def test_notebook_stdout_selected_seed_matches_manifest():
    import nbformat
    root=DEFAULT_PATH.parents[2]
    nb=nbformat.read(root/'notebooks/04_rl_q_learning_training.ipynb',as_version=4)
    stream=''.join(o.get('text','') for c in nb.cells if c.cell_type=='code' for o in c.get('outputs',[]) if o.output_type=='stream')
    seeds=re.findall(r'"selected_seed":\s*(\d+)',stream)
    selected=json.loads((DEFAULT_PATH/'manifest.json').read_text())['selected_seed']
    assert seeds and all(int(s)==selected for s in seeds)


def test_persisted_response_cannot_reintroduce_unknown_rl_action():
    from pydantic import ValidationError
    from backend.app.mas.agents.rl_decision import RLDecisionAgent
    from backend.app.schemas.runtime import WorkflowResponse
    registry=AgentRegistry()
    for a in [PredictionAgent(),KnowledgeAgent(),RLDecisionAgent(),EducationAgent(),SafetyAgent()]:registry.register(a)
    run=asyncio.run(Coordinator(registry).run(RunInput(question='What is diabetes?')))
    data=run.model_dump(mode='json')
    data['agent_results']['rl']['output']['action']='START_METFORMIN'
    with pytest.raises(ValidationError,match='non-whitelisted'):WorkflowResponse.model_validate(data)
