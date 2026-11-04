"""All input/evidence/policy fixtures are SYNTHETIC software tests, not clinical data."""
import asyncio
from dataclasses import replace
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.app.main import create_app
from backend.app.mas.coordinator import Coordinator
from backend.app.mas.registry import AgentRegistry, build_runtime_registry
from backend.app.mas.agents.runtime import (PredictionAgent, KnowledgeAgent, RLDecisionAgent,
    EducationAgent, SafetyAgent, ABSTENTION, REFUSAL, FAIL_CLOSED)
from backend.app.mas.repository import InMemoryRunRepository
from backend.app.mas.state import transition_agent, transition_workflow
from backend.app.schemas.contracts import (AgentName, AssessmentInput, EducationOutput,
    KnowledgeOutput, EvidenceItem, RLDecision)
from backend.app.schemas.runtime import *

SYNTHETIC = dict(pregnancies=0, glucose=100, blood_pressure=70, skin_thickness=20,
    insulin=50, bmi=22, diabetes_pedigree=0.3, age=30)

def run(payload=None, registry=None):
    return asyncio.run(Coordinator(registry).run(payload or RunInput(question="Tiểu đường là gì?")))

def registry_with(name, replacement=None, *, missing=False):
    registry = AgentRegistry()
    for agent in (PredictionAgent(), KnowledgeAgent(), RLDecisionAgent(), EducationAgent(), SafetyAgent()):
        if agent.definition.agent_id == name:
            if missing:
                continue
            agent = replacement
        registry.register(agent)
    return registry

@pytest.mark.parametrize("payload", [{}, {"question": "  "}, {"question": "x" * 4001},
    {"assessment": {"age": 30}}, {"question": "test", "unknown": True}, {"schema_version": "1.0", "question": "test"}])
def test_input_validation(payload):
    with pytest.raises(ValidationError):
        RunInput.model_validate(payload)

def test_typed_message_validation_and_roundtrip():
    message = AgentMessage(run_id=uuid4(), recipient=AgentName.knowledge, payload=KnowledgeTask(question="synthetic"))
    assert AgentMessage.model_validate_json(message.model_dump_json()) == message
    with pytest.raises(ValidationError):
        AgentMessage(run_id=uuid4(), recipient=AgentName.prediction, payload=KnowledgeTask(question="synthetic"))
    data = message.model_dump(mode="json")
    for key, value in [("recipient", "unknown"), ("run_id", "bad"), ("message_type", "result"), ("timestamp", "2026-01-01T00:00:00")]:
        with pytest.raises(ValidationError):
            AgentMessage.model_validate(data | {key: value})

def test_registry_contract_and_duplicates():
    registry = build_runtime_registry()
    assert len(registry.definitions()) == 5
    assert registry.get(AgentName.education).definition.input_schema is EducationTask
    assert all(spec.permitted_tools == () for spec in registry.definitions())
    with pytest.raises(ValueError, match="Duplicate"):
        registry.register(PredictionAgent())
    empty = AgentRegistry()
    assert empty.get(AgentName.prediction) is None
    agent = PredictionAgent()
    agent.definition = replace(agent.definition, timeout_seconds=0)
    with pytest.raises(ValueError, match="timeout"):
        empty.register(agent)

def test_no_assessment_no_prediction_and_knowledge_unavailable():
    result = run()
    assert result.status == WorkflowStatus.DEGRADED
    assert result.agent_results[AgentName.prediction].status == AgentStatus.SKIPPED
    assert result.agent_results[AgentName.knowledge].status == AgentStatus.UNAVAILABLE
    assert result.agent_results[AgentName.rl].status == AgentStatus.UNAVAILABLE
    assert result.agent_results[AgentName.education].status == AgentStatus.COMPLETED
    assert result.agent_results[AgentName.safety].status == AgentStatus.COMPLETED
    assert result.evidence == []
    assert "Không có kết quả mô hình" in result.response
    dispatched = [event.agent_id for event in result.agent_trace if event.reason == "TASK_DISPATCHED"]
    assert dispatched == [AgentName.safety, AgentName.knowledge, AgentName.education, AgentName.safety]

def test_assessment_only_prediction_unavailable_knowledge_skipped():
    result = run(RunInput(assessment=AssessmentInput(**SYNTHETIC)))
    assert result.agent_results[AgentName.prediction].status == AgentStatus.UNAVAILABLE
    assert result.agent_results[AgentName.prediction].output is None
    assert result.agent_results[AgentName.knowledge].status == AgentStatus.SKIPPED
    assert not any(e.agent_id == AgentName.knowledge and e.status == AgentStatus.RUNNING for e in result.agent_trace)

@pytest.mark.parametrize("cls,payload", [(PredictionAgent, PredictionTask(assessment=AssessmentInput(**SYNTHETIC))),
    (KnowledgeAgent, KnowledgeTask(question="synthetic")), (RLDecisionAgent, RLTask())])
def test_each_unintegrated_agent_is_unavailable(cls, payload):
    agent = cls()
    result = asyncio.run(agent.execute(AgentMessage(run_id=uuid4(), recipient=agent.definition.agent_id, payload=payload)))
    assert result.status == AgentStatus.UNAVAILABLE and result.implementation == "stub" and result.output is None

class SlowEducation(EducationAgent):
    definition = replace(EducationAgent.definition, timeout_seconds=0.001)
    async def execute(self, message):
        await asyncio.sleep(1)

class BrokenEducation(EducationAgent):
    async def execute(self, message):
        raise RuntimeError("SENSITIVE_EXCEPTION_MUST_NOT_LEAK")

@pytest.mark.parametrize("agent,error", [(SlowEducation(), "AGENT_TIMEOUT"), (BrokenEducation(), "AGENT_EXCEPTION_OR_INVALID_RESULT")])
def test_timeout_exception_and_education_fallback(agent, error):
    result = run(registry=registry_with(AgentName.education, agent))
    assert result.agent_results[AgentName.education].status == AgentStatus.FAILED
    assert result.agent_results[AgentName.education].errors == [error]
    assert result.status == WorkflowStatus.DEGRADED and result.response == ABSTENTION
    assert result.agent_results[AgentName.safety].status == AgentStatus.COMPLETED
    assert "SENSITIVE_EXCEPTION" not in result.model_dump_json()

@pytest.mark.parametrize("question", ["Tôi nên tăng liều insulin lên bao nhiêu?", "How many units of insulin should I take?", "Tôi nên tiêm bao nhiêu insulin?", "Stop my medication?"])
def test_medication_request_safety_veto(question):
    result = run(RunInput(question=question))
    assert result.status == WorkflowStatus.BLOCKED and result.response == REFUSAL
    assert "S01_MEDICATION_DOSING" in result.agent_results[AgentName.safety].output.rule_ids
    assert result.agent_results[AgentName.education].status == AgentStatus.SKIPPED
    assert result.agent_results[AgentName.education].output is None

class UnsafeEducation(EducationAgent):
    async def execute(self, message):
        return AgentResult(agent_id=AgentName.education, status=AgentStatus.COMPLETED, implementation="minimal",
            output=EducationOutput(text="Take 99 mg metformin. You definitely have diabetes.", evidence_ids=[]))

def test_output_safety_veto_redacts_rejected_text():
    result = run(registry=registry_with(AgentName.education, UnsafeEducation()))
    assert result.status == WorkflowStatus.BLOCKED
    assert "S02_DIAGNOSTIC_CERTAINTY" in result.agent_results[AgentName.safety].output.rule_ids
    assert "S03_OUTPUT_DOSAGE" in result.agent_results[AgentName.safety].output.rule_ids
    assert "99 mg" not in result.model_dump_json()

class BrokenSafety(SafetyAgent):
    async def execute(self, message):
        raise RuntimeError("failure")

@pytest.mark.parametrize("registry", [registry_with(AgentName.safety, BrokenSafety()), registry_with(AgentName.safety, missing=True)])
def test_safety_failure_and_missing_agent_fail_closed(registry):
    result = run(registry=registry)
    assert result.status == WorkflowStatus.FAILED and result.response == FAIL_CLOSED
    assert result.agent_results[AgentName.education].status == AgentStatus.SKIPPED

class HallucinatedCitation(EducationAgent):
    async def execute(self, message):
        return AgentResult(agent_id=AgentName.education, status=AgentStatus.COMPLETED, implementation="minimal",
            output=EducationOutput(text="Unsupported test-only claim", evidence_ids=["NONEXISTENT"]))

def test_unsupported_citation_is_not_released():
    result = run(registry=registry_with(AgentName.education, HallucinatedCitation()))
    assert result.status == WorkflowStatus.BLOCKED and result.evidence == []
    assert "Unsupported test-only claim" not in result.model_dump_json()
    assert "UNSUPPORTED_EDUCATION_CITATION" in result.warnings

def test_trace_order_correlation_and_state_guards():
    result = run(RunInput(assessment=AssessmentInput(**SYNTHETIC), question="synthetic"))
    assert [e.sequence for e in result.agent_trace] == list(range(1, len(result.agent_trace)+1))
    assert all(e.run_id == result.run_id for e in result.agent_trace)
    assert result.agent_trace[0].status == WorkflowStatus.RUNNING
    assert result.agent_trace[-1].status == result.status
    assert [e.agent_id for e in result.agent_trace if e.reason == "TASK_DISPATCHED"] == [
        AgentName.safety, AgentName.prediction, AgentName.knowledge, AgentName.education, AgentName.safety]
    starts = [e for e in result.agent_trace if e.reason == "TASK_DISPATCHED"]
    assert len({e.message_id for e in starts}) == len(starts)
    for start in starts:
        terminal = [e for e in result.agent_trace if e.message_id == start.message_id and e.sequence > start.sequence]
        assert len(terminal) == 1 and terminal[0].agent_id == start.agent_id
    state = WorkflowState(request=RunInput(question="synthetic"))
    with pytest.raises(ValueError, match="Illegal workflow"):
        transition_workflow(state, WorkflowStatus.COMPLETED)
    state.agent_results[AgentName.education] = AgentResult(agent_id=AgentName.education, status=AgentStatus.SKIPPED, implementation="minimal")
    with pytest.raises(ValueError, match="Illegal agent"):
        transition_agent(state, AgentResult(agent_id=AgentName.education, status=AgentStatus.RUNNING, implementation="minimal"), "test")

def test_concurrent_coordinator_runs_are_isolated():
    async def scenario():
        coordinator = Coordinator()
        return await asyncio.gather(*(coordinator.run(RunInput(question="synthetic")) for _ in range(20)))
    results = asyncio.run(scenario())
    assert len({r.run_id for r in results}) == 20
    results[0].warnings.append("MUTATION_TEST")
    results[0].agent_results[AgentName.safety].errors.append("MUTATION_TEST")
    for result in results[1:]:
        assert "MUTATION_TEST" not in result.model_dump_json()
        assert all(e.run_id == result.run_id for e in result.agent_trace)

def test_repository_copy_eviction_and_app_isolation():
    repository = InMemoryRunRepository(max_runs=1)
    first, second = run(), run()
    repository.save(first)
    snapshot = repository.get(first.run_id)
    snapshot.warnings.append("MUTATION_TEST")
    assert "MUTATION_TEST" not in repository.get(first.run_id).warnings
    repository.save(second)
    assert repository.get(first.run_id) is None
    assert create_app(prediction_enabled=False).state.run_repository.get(second.run_id) is None

def test_api_routes_validation_readback_and_cors():
    with TestClient(create_app(prediction_enabled=False)) as client:
        response = client.post("/api/v1/mas/runs", json={"question": "Tiểu đường là gì?"})
        assert response.status_code == 201
        result = response.json()
        assert result["schema_version"] == "2.4" and result["evidence"] == []
        run_id = result["run_id"]
        assert client.get(f"/api/v1/mas/runs/{run_id}").json() == result
        trace = client.get(f"/api/v1/mas/runs/{run_id}/trace").json()
        assert trace["agent_trace"] == result["agent_trace"] and trace["run_id"] == run_id
        assert client.get(f"/api/v1/mas/runs/{uuid4()}").status_code == 404
        assert client.get("/api/v1/mas/runs/bad-uuid").status_code == 422
        assert client.post("/api/v1/mas/runs", json={}).status_code == 422
        assert client.post("/api/v1/mas/runs", json={"assessment": {"age": 1}}).status_code == 422
        agents = client.get("/api/v1/mas/agents").json()["agents"]
        assert len(agents) == 5 and sum(a["implementation"] == "stub" for a in agents) == 3
        assert all(a["input_schema"] and a["output_schema"] and a["fallback_policy"] for a in agents)
        cors = client.options("/api/v1/mas/runs", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
        assert cors.status_code == 200 and "POST" in cors.headers["access-control-allow-methods"]

def test_concurrent_http_requests_do_not_share_state():
    async def scenario():
        app = create_app(prediction_enabled=False)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            responses = await asyncio.gather(*(client.post("/api/v1/mas/runs", json={"question": "synthetic"}) for _ in range(12)))
            assert all(response.status_code == 201 for response in responses)
            results = [response.json() for response in responses]
            assert len({r["run_id"] for r in results}) == 12
            for result in results:
                assert all(event["run_id"] == result["run_id"] for event in result["agent_trace"])
                fetched = await client.get(f"/api/v1/mas/runs/{result['run_id']}")
                assert fetched.json() == result
    asyncio.run(scenario())

# Explicit synthetic evidence/policy injection checks routing, not a real integration.
class SyntheticKnowledge(KnowledgeAgent):
    def __init__(self):
        super().__init__()
        self.definition = replace(self.definition, implementation="minimal", available=True)
    async def execute(self, message):
        return AgentResult(agent_id=AgentName.knowledge, status=AgentStatus.COMPLETED, implementation="minimal",
            output=KnowledgeOutput(evidence=[EvidenceItem(evidence_id="SYNTHETIC_TEST_ONLY", source_title="Synthetic test fixture", source_url="https://example.org", publisher="Test", section="Test", retrieved_at="2026-01-01T00:00:00Z", excerpt="Synthetic routing test; not medical evidence")]))

class SyntheticPolicy(RLDecisionAgent):
    def __init__(self):
        super().__init__()
        self.definition = replace(self.definition, implementation="minimal", available=True)
    async def execute(self, message):
        assert message.payload.evidence[0].evidence_id == "SYNTHETIC_TEST_ONLY"
        return AgentResult(agent_id=AgentName.rl, status=AgentStatus.COMPLETED, implementation="minimal",
            output=RLDecision(state={}, action="SHOW_EVIDENCE", policy_version="test", decision_source="policy"))

def test_compatible_policy_only_runs_with_valid_context():
    registry = registry_with(AgentName.rl, SyntheticPolicy())
    result = run(registry=registry)
    assert result.agent_results[AgentName.rl].status == AgentStatus.SKIPPED
    registry = AgentRegistry()
    for agent in (PredictionAgent(), SyntheticKnowledge(), SyntheticPolicy(), EducationAgent(), SafetyAgent()):
        registry.register(agent)
    result = run(registry=registry)
    assert result.agent_results[AgentName.rl].status == AgentStatus.COMPLETED
    assert result.agent_results[AgentName.rl].output.policy_version == "test"
