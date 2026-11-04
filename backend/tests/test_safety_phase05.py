"""Synthetic adversarial software fixtures only; no clinical validation claims."""
import asyncio,json
from pathlib import Path
from dataclasses import replace
import pytest
from backend.app.rules.engine import RuleEngine,Context,RULES
from backend.app.schemas.runtime import RunInput,WorkflowState,AgentResult,AgentStatus,EducationTask,AgentMessage,WorkflowStatus
from backend.app.schemas.contracts import AgentName,EducationOutput
from backend.app.mas.coordinator import Coordinator
from backend.app.mas.registry import build_runtime_registry,AgentRegistry
from backend.app.mas.agents.safety import SafetyAgent
from backend.app.mas.agents.runtime import PredictionAgent,KnowledgeAgent,RLDecisionAgent,EducationAgent
CASES=json.loads((Path(__file__).parent/'fixtures/safety_scenarios.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_rule_scenario(case):
    engine=RuleEngine(); c=Context(**case['context']);first=engine.evaluate(c);second=engine.evaluate(c)
    assert first.decision==case['expected_decision']
    if case['expected_rule']:assert case['expected_rule'] in first.rule_ids
    assert first.model_dump(exclude={'timestamp'})==second.model_dump(exclude={'timestamp'})
    assert first.reason and first.checked_content and first.policy_version=='safety-1.1'
    assert c.question not in first.checked_content if len(c.question)>5 else True

def test_rules_metadata_and_config_errors():
    assert len({r.rule_id for r in RULES})==len(RULES)
    assert {r.category for r in RULES}=={'input','workflow','output','evidence','escalation'}
    assert all(r.description and r.version and r.priority>0 and callable(r.condition) for r in RULES)
    with pytest.raises(ValueError):RuleEngine(())
    with pytest.raises(ValueError):RuleEngine((RULES[0],RULES[0]))

@pytest.mark.parametrize('question,decision',[('What is diabetes?','ALLOW'),('Prescribe metformin','BLOCK'),('My father is unconscious','ESCALATE'),('Predict my risk','REQUEST_CLARIFICATION')])
def test_two_gate_coordinator_and_early_veto(question,decision):
    result=asyncio.run(Coordinator().run(RunInput(question=question)))
    assert [d.stage for d in result.safety_decisions]==['input','output']
    assert result.safety_decisions[0].decision==decision
    gates=[e for e in result.agent_trace if e.reason.startswith('SAFETY_GATE_')]
    assert len(gates)==2 and all(e.rule_ids and e.safety_decision for e in gates)
    if decision in ('BLOCK','ESCALATE','REQUEST_CLARIFICATION'):
        assert result.status==WorkflowStatus.BLOCKED
        assert all(result.agent_results[a].status==AgentStatus.SKIPPED for a in [AgentName.prediction,AgentName.knowledge,AgentName.rl,AgentName.education])

def make_registry(safety,education=None):
    registry=AgentRegistry()
    for a in [PredictionAgent(),KnowledgeAgent(),RLDecisionAgent(),education or EducationAgent(),safety]:registry.register(a)
    return registry

class BrokenSafety(SafetyAgent):
    async def execute(self,message):raise RuntimeError('SENSITIVE_TEST_EXCEPTION')
class SlowSafety(SafetyAgent):
    definition=replace(SafetyAgent.definition,timeout_seconds=0.001)
    async def execute(self,message):await asyncio.sleep(1)

@pytest.mark.parametrize('agent',[BrokenSafety(),SlowSafety()])
def test_safety_failure_no_business_actions(agent):
    result=asyncio.run(Coordinator(make_registry(agent)).run(RunInput(question='What is diabetes?')))
    assert result.status==WorkflowStatus.FAILED
    assert any('SYS01_SAFETY_FAILURE' in e.rule_ids for e in result.agent_trace)
    assert result.agent_results[AgentName.knowledge].status==AgentStatus.SKIPPED
    assert 'SENSITIVE_TEST_EXCEPTION' not in result.model_dump_json()

class UnsafeEducation(EducationAgent):
    async def execute(self,message):return AgentResult(agent_id=AgentName.education,status=AgentStatus.COMPLETED,implementation='minimal',output=EducationOutput(text='You definitely have diabetes; take 77 mg',evidence_ids=[]))

def test_output_veto_redacts_unsafe_output():
    result=asyncio.run(Coordinator(make_registry(SafetyAgent(),UnsafeEducation())).run(RunInput(question='What is diabetes?')))
    assert result.status==WorkflowStatus.BLOCKED
    assert '77 mg' not in result.model_dump_json()
    assert 'S02_DIAGNOSTIC_CERTAINTY' in result.safety_decisions[-1].rule_ids

def test_dispatch_and_finalization_cannot_bypass_safety():
    state=WorkflowState(request=RunInput(question='Synthetic question'))
    coordinator=Coordinator()
    with pytest.raises(ValueError,match='SAFETY_PREFLIGHT_REQUIRED'):
        asyncio.run(coordinator.dispatch(state,AgentName.education,EducationTask()))
    with pytest.raises(ValueError,match='BOTH_SAFETY_GATES_REQUIRED'):
        coordinator.finish(state,WorkflowStatus.COMPLETED,'unreviewed',[])

class AlwaysAllow(SafetyAgent):
    async def execute(self,message):
        from backend.app.schemas.safety import SafetyDecision
        return AgentResult(agent_id=AgentName.safety,status=AgentStatus.COMPLETED,implementation='integrated',output=SafetyDecision(allowed=True,decision='ALLOW',severity='info',rule_ids=['SYNTHETIC_BYPASS_ATTEMPT'],reason='Synthetic fake safety',checked_content='fixture',stage=message.payload.stage))

def test_replaced_safety_cannot_downgrade_mandatory_rules():
    result=asyncio.run(Coordinator(make_registry(AlwaysAllow())).run(RunInput(question='Prescribe metformin')))
    assert result.status==WorkflowStatus.BLOCKED and result.safety_decisions[0].decision=='BLOCK'


class FailedOutputSafety(SafetyAgent):
    async def execute(self,message):
        if message.payload.stage=='output':raise RuntimeError('SYNTHETIC_OUTPUT_FAILURE')
        return await super().execute(message)

def test_output_gate_failure_withholds_completed_education():
    result=asyncio.run(Coordinator(make_registry(FailedOutputSafety())).run(RunInput(question='What is diabetes?')))
    assert result.status==WorkflowStatus.FAILED
    assert result.agent_results[AgentName.education].output.text=='[WITHHELD_BY_SAFETY]'
    assert result.safety_decisions[-1].rule_ids==['SYS01_SAFETY_FAILURE']

def test_rl_action_cannot_override_safety():
    from backend.app.schemas.contracts import KnowledgeOutput,EvidenceItem,RLDecision
    from backend.app.knowledge.store import documents
    from backend.app.mas.agents.knowledge import EducationAgent as GroundedEducation
    class TestKnowledge(KnowledgeAgent):
        def __init__(self):
            super().__init__();self.definition=replace(self.definition,implementation='integrated',available=True)
        async def execute(self,message):
            c=documents()[0]
            e=EvidenceItem(evidence_id=c['id'],source_title=c['title'],source_url=c['url'],publisher=c['publisher'],section=c['section'],retrieved_at=c['retrieved_at'],excerpt=c['text'])
            return AgentResult(agent_id=AgentName.knowledge,status=AgentStatus.COMPLETED,implementation='integrated',output=KnowledgeOutput(evidence=[e]))
    class TestPolicy(RLDecisionAgent):
        def __init__(self):
            super().__init__();self.definition=replace(self.definition,implementation='integrated',available=True)
        async def execute(self,message):
            return AgentResult(agent_id=AgentName.rl,status=AgentStatus.COMPLETED,implementation='integrated',output=RLDecision(state={},action='adjust_insulin_dose_SYNTHETIC_TEST_ONLY',policy_version='synthetic-test',decision_source='policy'))
    registry=AgentRegistry()
    for a in [PredictionAgent(),TestKnowledge(),TestPolicy(),GroundedEducation(),SafetyAgent()]:registry.register(a)
    result=asyncio.run(Coordinator(registry).run(RunInput(question='What is diabetes?')))
    assert result.status==WorkflowStatus.BLOCKED
    assert 'W04_ACTION_NOT_ALLOWED' in result.safety_decisions[-1].rule_ids
    assert result.agent_results[AgentName.rl].output is None
    assert result.agent_results[AgentName.rl].errors==['RL_ACTION_NOT_ALLOWED']
    assert 'adjust_insulin_dose' not in result.model_dump_json()

@pytest.mark.parametrize('version',['2.0','2.1','2.2','2.3'])
def test_explicit_old_runtime_version_is_rejected(version):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):RunInput(schema_version=version,question='Synthetic question')


def test_snapshot_missing_safety_audit_is_rejected():
    from pydantic import ValidationError
    from backend.app.schemas.runtime import WorkflowResponse
    result=asyncio.run(Coordinator().run(RunInput(question='What is diabetes?')))
    data=result.model_dump(mode='json');data['safety_decisions']=[]
    with pytest.raises(ValidationError):WorkflowResponse.model_validate(data)

def test_snapshot_veto_cannot_be_relabelled_completed():
    from pydantic import ValidationError
    from backend.app.schemas.runtime import WorkflowResponse
    result=asyncio.run(Coordinator().run(RunInput(question='Prescribe metformin')))
    data=result.model_dump(mode='json');data['status']='COMPLETED'
    with pytest.raises(ValidationError):WorkflowResponse.model_validate(data)


def test_forged_quote_on_official_host_is_blocked():
    from backend.app.schemas.contracts import KnowledgeOutput,EvidenceItem
    from backend.app.knowledge.store import documents
    from backend.app.mas.agents.knowledge import EducationAgent as GroundedEducation
    class ForgedKnowledge(KnowledgeAgent):
        def __init__(self):
            super().__init__();self.definition=replace(self.definition,implementation='integrated',available=True)
        async def execute(self,message):
            c=documents()[0]
            e=EvidenceItem(evidence_id=c['id'],source_title=c['title'],source_url=c['url'],publisher=c['publisher'],section=c['section'],retrieved_at=c['retrieved_at'],excerpt='SYNTHETIC FORGED QUOTE NOT FOUND IN THE SOURCE')
            return AgentResult(agent_id=AgentName.knowledge,status=AgentStatus.COMPLETED,implementation='integrated',output=KnowledgeOutput(evidence=[e]))
    registry=AgentRegistry()
    for a in [PredictionAgent(),ForgedKnowledge(),RLDecisionAgent(),GroundedEducation(),SafetyAgent()]:registry.register(a)
    result=asyncio.run(Coordinator(registry).run(RunInput(question='What is diabetes?')))
    assert result.status==WorkflowStatus.BLOCKED
    assert 'E01_INVALID_PROVENANCE' in result.safety_decisions[-1].rule_ids
    assert 'SYNTHETIC FORGED QUOTE' not in result.model_dump_json()
