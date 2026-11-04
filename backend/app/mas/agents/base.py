from dataclasses import dataclass
from backend.app.schemas.contracts import AgentMessage, AgentName, AgentResult

@dataclass(frozen=True)
class AgentSpec:
    name: AgentName
    responsibility: str
    input_contract: str
    output_contract: str
    decision_policy: str
    planned_tools: tuple[str, ...]
    enabled_tools: tuple[str, ...] = ()

class StubAgent:
    def __init__(self, spec: AgentSpec):
        self.spec = spec

    async def run(self, message: AgentMessage) -> AgentResult:
        if message.recipient != self.spec.name or message.message_type != "task":
            raise ValueError("Invalid task recipient or message type")
        return AgentResult(agent_name=self.spec.name, status="stub", errors=["NOT_IMPLEMENTED_PHASE_00"])


from typing import Protocol
from pydantic import BaseModel
from backend.app.schemas.runtime import AgentMessage as RuntimeMessage, AgentResult as RuntimeResult

@dataclass(frozen=True)
class AgentDefinition:
    agent_id: AgentName
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    permitted_tools: tuple[str, ...] = ()
    implementation: str = "stub"
    available: bool = False
    timeout_seconds: float = 1.0
    fallback_policy: str = "Return UNAVAILABLE; coordinator continues without business output"
    status_semantics: str = "NOT_STARTED -> RUNNING -> COMPLETED/FAILED/UNAVAILABLE; conditional SKIPPED"

class BaseAgent(Protocol):
    definition: AgentDefinition

    async def execute(self, message: RuntimeMessage) -> RuntimeResult:
        ...
