import asyncio
from uuid import uuid4
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.app.main import create_app
app = create_app(prediction_enabled=False)  # Explicit legacy Phase 00/01 scaffold regression.
from backend.app.schemas.contracts import *
from backend.app.mas.registry import SPECS, build_registry
from backend.app.mas.legacy import Coordinator

# Synthetic fixture only; not a real patient or a clinical reference.
SYNTHETIC = dict(pregnancies=0, glucose=100, blood_pressure=70, skin_thickness=20,
                 insulin=50, bmi=22, diabetes_pedigree=0.3, age=30)

def test_health_and_capabilities():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        components = client.get("/api/v1/system/capabilities").json()["components"]
        assert components["prediction_agent"] == "stub"
        assert set(components.values()) <= {"available", "unavailable", "stub"}
        assert client.post("/api/v1/predict", json=SYNTHETIC).status_code == 404

@pytest.mark.parametrize("change", [{"glucose": -1}, {"bmi": float("nan")}, {"age": 1.2}, {"unexpected": 1}])
def test_invalid_assessment(change):
    with pytest.raises(ValidationError):
        AssessmentInput(**(SYNTHETIC | change))

def test_schema_roundtrip():
    request = AssessmentInput(**SYNTHETIC)
    state = WorkflowState(request=request)
    assert WorkflowState.model_validate_json(state.model_dump_json()) == state
    evidence = EvidenceItem(evidence_id="synthetic-contract-test", source_title="Synthetic fixture", source_url="https://example.org", publisher="Test", section="test", retrieved_at="2026-01-01T00:00:00Z", excerpt="Synthetic schema test only")
    objects = [AgentMessage(run_id=state.run_id, sender="coordinator", recipient="prediction", message_type="task", payload={}),
        AgentResult(agent_name="prediction", status="stub"),
        PredictionResult(model_id="test-only", model_version="0", predicted_class=0, score=0.5, limitations=["Synthetic contract fixture; no inference"]),
        evidence, RLDecision(state={}, action="test", policy_version="test", decision_source="fallback"),
        SafetyDecision(allowed=False, severity="warning", rule_ids=[], reason="Test fixture"),
        WorkflowResponse(run_id=state.run_id, status="stub", response="Not implemented")]
    for obj in objects:
        assert type(obj).model_validate_json(obj.model_dump_json()) == obj

@pytest.mark.parametrize("spec", SPECS, ids=lambda spec: spec.name.value)
def test_each_agent_contract_and_stub(spec):
    assert spec.responsibility and spec.input_contract and spec.output_contract and spec.decision_policy
    assert spec.enabled_tools == ()
    message = AgentMessage(run_id=uuid4(), sender="coordinator", recipient=spec.name, message_type="task", payload={})
    result = asyncio.run(build_registry()[spec.name].run(message))
    assert result.agent_name == spec.name and result.status == "stub" and result.output is None
    message.recipient = "coordinator"
    with pytest.raises(ValueError):
        asyncio.run(build_registry()[spec.name].run(message))

def test_dispatch_trace_and_failures():
    state = WorkflowState(request=AssessmentInput(**SYNTHETIC))
    coordinator = Coordinator(timeout_seconds=0.001)
    assert asyncio.run(coordinator.dispatch(state, AgentName.prediction)).status == "stub"
    class Slow:
        async def run(self, message):
            await asyncio.sleep(1)
    coordinator.registry[AgentName.prediction] = Slow()
    assert asyncio.run(coordinator.dispatch(state, AgentName.prediction)).status == "timeout"
    class Broken:
        async def run(self, message):
            raise RuntimeError("test")
    coordinator.registry[AgentName.prediction] = Broken()
    assert asyncio.run(coordinator.dispatch(state, AgentName.prediction)).status == "error"
    del coordinator.registry[AgentName.prediction]
    assert asyncio.run(coordinator.dispatch(state, AgentName.prediction)).status == "unavailable"
    assert len(state.trace) == 4 and state.final_response is None

def test_env_example_uses_placeholders():
    entries = dict(line.split("=", 1) for line in Path(".env.example").read_text().splitlines() if "=" in line)
    for key, value in entries.items():
        if any(word in key for word in ("PASSWORD", "SECRET", "TOKEN", "KEY")):
            assert value.startswith("REPLACE_")
    assert "REPLACE_PASSWORD" in entries["DATABASE_URL"]

def test_cors():
    with TestClient(app) as client:
        response = client.get("/health", headers={"Origin": "http://localhost:5173"})
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "access-control-allow-origin" not in client.get("/health", headers={"Origin": "https://untrusted.example"}).headers


@pytest.mark.parametrize("name,output", [
    (AgentName.prediction, PredictionResult(model_id="synthetic-test", model_version="0", predicted_class=0, score=0.5, limitations=["Synthetic contract fixture only"])),
    (AgentName.knowledge, KnowledgeOutput(evidence=[])),
    (AgentName.education, EducationOutput(text="Synthetic contract fixture only", evidence_ids=[])),
    (AgentName.safety, SafetyDecision(allowed=False, severity="warning", rule_ids=[], reason="Synthetic fixture")),
    (AgentName.rl, RLDecision(state={}, action="synthetic-test", policy_version="0", decision_source="fallback")),
])
def test_agent_output_invariants(name, output):
    result = AgentResult(agent_name=name, status="success", output=output)
    assert AgentResult.model_validate_json(result.model_dump_json()) == result
    with pytest.raises(ValidationError):
        AgentResult(agent_name=name, status="success")
    with pytest.raises(ValidationError):
        AgentResult(agent_name=name, status="stub", output=output)
    with pytest.raises(ValidationError):
        AgentResult(agent_name=name, status="success", output=output, errors=["FAIL"])
    wrong_name = AgentName.safety if name != AgentName.safety else AgentName.prediction
    with pytest.raises(ValidationError):
        AgentResult(agent_name=wrong_name, status="success", output=output)
