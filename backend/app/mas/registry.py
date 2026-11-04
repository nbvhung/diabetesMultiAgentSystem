from backend.app.schemas.contracts import AgentName
from backend.app.mas.agents.base import AgentSpec, StubAgent

SPECS = (
    AgentSpec(AgentName.prediction, "Estimate risk using versioned DL inference", "AssessmentInput", "PredictionResult", "Require validated features and loaded model; otherwise unavailable", ("torch_inference",)),
    AgentSpec(AgentName.knowledge, "Retrieve attributable knowledge", "AssessmentInput + query", "KnowledgeOutput", "Only return retrieved evidence with provenance", ("neo4j_read", "rag_retrieve")),
    AgentSpec(AgentName.education, "Explain risk and educational actions with citations", "PredictionResult + KnowledgeOutput + RLDecision", "EducationOutput", "Use supported evidence; abstain without evidence", ("evidence_read",)),
    AgentSpec(AgentName.safety, "Check safety before releasing content", "AssessmentInput + proposed education", "SafetyDecision", "Block unsafe content; fail closed on missing rules", ("rule_evaluate",)),
    AgentSpec(AgentName.rl, "Select educational action", "Validated educational state", "RLDecision", "Versioned allowed-action policy; explicit fallback only", ("policy_inference",)),
)

def build_registry() -> dict[AgentName, StubAgent]:
    return {spec.name: StubAgent(spec) for spec in SPECS}


from math import isfinite
from backend.app.mas.agents.base import BaseAgent
from backend.app.mas.agents.runtime import PredictionAgent, KnowledgeAgent, RLDecisionAgent, EducationAgent, SafetyAgent

class AgentRegistry:
    def __init__(self):
        self._agents: dict[AgentName, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        spec = agent.definition
        if spec.agent_id in self._agents:
            raise ValueError(f"Duplicate agent: {spec.agent_id}")
        if not isfinite(spec.timeout_seconds) or spec.timeout_seconds <= 0:
            raise ValueError("Agent timeout must be finite and positive")
        self._agents[spec.agent_id] = agent

    def get(self, agent_id: AgentName) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def definitions(self):
        return tuple(agent.definition for agent in self._agents.values())

def build_runtime_registry() -> AgentRegistry:
    registry = AgentRegistry()
    from backend.app.mas.agents.safety import SafetyAgent
    for agent in (PredictionAgent(), KnowledgeAgent(), RLDecisionAgent(), EducationAgent(), SafetyAgent()):
        registry.register(agent)
    return registry
