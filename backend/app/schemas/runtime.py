"""Runtime v2.4. Phase 00 contracts.py remains unchanged and importable."""
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator
from backend.app.schemas.contracts import (AgentName, AssessmentInput, PredictionResult,
    KnowledgeOutput, EducationOutput, SafetyDecision, RLDecision, EvidenceItem)

from backend.app.schemas.education import EducationOutput as PlannedEducationOutput
from backend.app.schemas.safety import SafetyDecision as PolicySafetyDecision
from backend.app.schemas.prediction import PredictionResult as ServingPrediction

class RuntimeContract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal["2.4"] = "2.4"

class AgentStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"

class WorkflowStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"

class RunInput(RuntimeContract):
    is_synthetic: Literal[True] | None = None
    assessment: AssessmentInput | None = None
    question: Annotated[str, Field(min_length=1, max_length=4000)] | None = None

    @model_validator(mode="after")
    def require_input(self):
        if self.question is not None:
            self.question = self.question.strip()
            if not self.question:
                raise ValueError("Question must not be blank")
        if self.assessment is None and self.question is None:
            raise ValueError("Provide assessment or question")
        return self

class PredictionTask(RuntimeContract):
    assessment: AssessmentInput

class KnowledgeTask(RuntimeContract):
    question: Annotated[str, Field(min_length=1, max_length=4000)]

class RLTask(RuntimeContract):
    simulated_knowledge_level: Literal['low','medium','high'] = 'medium'
    simulated_engagement_level: Literal['low','medium','high'] = 'medium'
    safety_status: Literal['normal','restricted'] = 'normal'

    prediction: PredictionResult | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)

class EducationTask(RuntimeContract):
    question: str | None = None
    prediction: PredictionResult | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    decision: RLDecision | None = None
    warnings: list[str] = Field(default_factory=list)

class SafetyTask(RuntimeContract):
    question: str | None = None
    candidate: str = ''
    stage: Literal['input','output'] = 'output'
    assessment: dict | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    cited_ids: list[str] = Field(default_factory=list)
    trusted_evidence: bool = True
    grounded: bool = False
    abstention: bool = False
    prediction_present: bool = False
    knowledge_available: bool = True
    action: str = ''

INPUT_TYPES = {AgentName.prediction: PredictionTask, AgentName.knowledge: KnowledgeTask,
    AgentName.rl: RLTask, AgentName.education: EducationTask, AgentName.safety: SafetyTask}
OUTPUT_TYPES = {AgentName.prediction: PredictionResult, AgentName.knowledge: KnowledgeOutput,
    AgentName.rl: RLDecision, AgentName.education: EducationOutput, AgentName.safety: SafetyDecision}

class AgentMessage(RuntimeContract):
    message_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    sender: Literal["coordinator"] = "coordinator"
    recipient: AgentName
    message_type: Literal["task"] = "task"
    payload: PredictionTask | KnowledgeTask | RLTask | EducationTask | SafetyTask
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_recipient(self):
        if not isinstance(self.payload, INPUT_TYPES[self.recipient]):
            raise ValueError("Payload does not match recipient input_schema")
        return self

class AgentResult(RuntimeContract):
    agent_id: AgentName
    status: AgentStatus
    implementation: Literal["stub", "minimal", "integrated"]
    output: PlannedEducationOutput | PolicySafetyDecision | ServingPrediction | PredictionResult | KnowledgeOutput | EducationOutput | SafetyDecision | RLDecision | None = None
    errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_output(self):
        if self.status == AgentStatus.COMPLETED:
            if self.implementation == "stub" or not isinstance(self.output, OUTPUT_TYPES[self.agent_id]) or self.errors:
                raise ValueError("COMPLETED requires a non-stub typed output and no errors")
        elif self.output is not None:
            raise ValueError("Non-completed result cannot contain output")
        return self

class TraceEvent(RuntimeContract):
    sequence: int = Field(ge=1)
    run_id: UUID
    agent_id: AgentName | None = None
    message_id: UUID | None = None
    status: AgentStatus | WorkflowStatus
    reason: str
    rule_ids: list[str] = Field(default_factory=list)
    safety_decision: str | None = None
    safety_stage: str | None = None
    policy_version: str | None = None
    proposed_action: str | None = None
    effective_action: str | None = None
    action_override_reason: str | None = None
    action: str | None = None
    decision_source: str | None = None
    model_version: str | None = None
    inference_latency_ms: float | None = None
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WorkflowState(RuntimeContract):
    run_id: UUID = Field(default_factory=uuid4)
    request: RunInput
    status: WorkflowStatus = WorkflowStatus.NOT_STARTED
    agent_results: dict[AgentName, AgentResult] = Field(default_factory=dict)
    trace: list[TraceEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    safety_decisions: list[PolicySafetyDecision] = Field(default_factory=list)
    final_response: str | None = None

class WorkflowResponse(RuntimeContract):
    run_id: UUID
    status: WorkflowStatus
    agent_results: dict[AgentName, AgentResult]
    response: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    agent_trace: list[TraceEvent]
    warnings: list[str]
    limitations: list[str]
    safety_decisions: list[PolicySafetyDecision] = Field(default_factory=list)


    @model_validator(mode='after')
    def enforce_safety_audit(self):
        if [d.stage for d in self.safety_decisions] != ['input','output']:
            raise ValueError('Terminal run requires both ordered safety decisions')
        from backend.app.rl.mdp import ACTIONS
        rl=self.agent_results.get(AgentName.rl)
        if rl is not None and rl.status==AgentStatus.COMPLETED:
            withheld=self.status in {WorkflowStatus.BLOCKED,WorkflowStatus.FAILED} and rl.output.action=='WITHHELD_BY_SAFETY'
            if rl.output.action not in ACTIONS and not withheld:
                raise ValueError('Runtime response contains non-whitelisted RL action')
        if self.status in {WorkflowStatus.COMPLETED,WorkflowStatus.DEGRADED} and any(not d.allowed for d in self.safety_decisions):
            raise ValueError('Safety veto cannot coexist with released workflow')
        return self
