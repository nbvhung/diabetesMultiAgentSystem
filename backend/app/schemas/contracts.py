from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, AwareDatetime, JsonValue, model_validator

class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal["1.0"] = "1.0"

class AgentName(str, Enum):
    prediction = "prediction"
    knowledge = "knowledge"
    education = "education"
    safety = "safety"
    rl = "rl"

class AssessmentInput(Contract):
    pregnancies: Annotated[int, Field(ge=0, strict=True)]
    glucose: Annotated[float, Field(ge=0)]
    blood_pressure: Annotated[float, Field(ge=0)]
    skin_thickness: Annotated[float, Field(ge=0)]
    insulin: Annotated[float, Field(ge=0)]
    bmi: Annotated[float, Field(ge=0)]
    diabetes_pedigree: Annotated[float, Field(ge=0)]
    age: Annotated[int, Field(ge=1, strict=True)]

class AgentMessage(Contract):
    message_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    sender: Literal["coordinator"] | AgentName
    recipient: Literal["coordinator"] | AgentName
    message_type: Literal["task", "result", "error"]
    payload: dict[str, JsonValue]
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PredictionResult(Contract):
    model_id: str
    model_version: str
    predicted_class: Literal[0, 1]
    score: Annotated[float, Field(ge=0, le=1)]
    limitations: Annotated[list[str], Field(min_length=1)]

class EvidenceItem(Contract):
    evidence_id: str
    source_title: str
    source_url: HttpUrl
    publisher: str
    section: str
    retrieved_at: AwareDatetime
    excerpt: str

class RLDecision(Contract):
    state: dict[str, JsonValue]
    action: str
    policy_version: str
    decision_source: Literal["policy", "fallback"]

class SafetyDecision(Contract):
    allowed: bool
    severity: Literal["info", "warning", "critical"]
    rule_ids: list[str]
    reason: str

class EducationOutput(Contract):
    text: str
    evidence_ids: list[str]

class KnowledgeOutput(Contract):
    evidence: list[EvidenceItem]

class AgentResult(Contract):
    agent_name: AgentName
    status: Literal["success", "stub", "unavailable", "error", "timeout"]
    output: PredictionResult | KnowledgeOutput | EducationOutput | SafetyDecision | RLDecision | None = None
    errors: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_output_contract(self):
        expected = {
            AgentName.prediction: PredictionResult,
            AgentName.knowledge: KnowledgeOutput,
            AgentName.education: EducationOutput,
            AgentName.safety: SafetyDecision,
            AgentName.rl: RLDecision,
        }
        if self.status == "success":
            if not isinstance(self.output, expected[self.agent_name]):
                raise ValueError("Successful agent output must match its output contract")
            if self.errors:
                raise ValueError("Successful agent result cannot contain errors")
        elif self.output is not None:
            raise ValueError("Non-success agent result must not contain business output")
        return self

class TraceEvent(Contract):
    agent_name: AgentName
    status: Literal["stub", "unavailable", "error", "timeout", "success"]
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkflowState(Contract):
    run_id: UUID = Field(default_factory=uuid4)
    request: AssessmentInput
    agent_results: dict[AgentName, AgentResult] = Field(default_factory=dict)
    trace: list[TraceEvent] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    final_response: str | None = None

class WorkflowResponse(Contract):
    run_id: UUID
    status: Literal["completed", "stub", "failed"]
    response: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    agent_trace: list[TraceEvent] = Field(default_factory=list)
