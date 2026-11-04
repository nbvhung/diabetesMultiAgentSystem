"""Phase 00 scaffold: dispatch one stub task; no clinical workflow is integrated."""
import asyncio
import logging
from backend.app.mas.registry import build_registry
from backend.app.schemas.contracts import AgentMessage, AgentName, AgentResult, TraceEvent, WorkflowState

logger = logging.getLogger(__name__)

class Coordinator:
    def __init__(self, timeout_seconds: float = 1.0):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = timeout_seconds
        self.registry = build_registry()

    async def dispatch(self, state: WorkflowState, name: AgentName) -> AgentResult:
        message = AgentMessage(run_id=state.run_id, sender="coordinator", recipient=name,
                               message_type="task", payload=state.request.model_dump(mode="json"))
        try:
            agent = self.registry.get(name)
            if agent is None:
                result = AgentResult(agent_name=name, status="unavailable", errors=["AGENT_UNREGISTERED"])
            else:
                result = await asyncio.wait_for(agent.run(message), self.timeout_seconds)
        except TimeoutError:
            result = AgentResult(agent_name=name, status="timeout", errors=["AGENT_TIMEOUT"])
        except Exception:
            logger.error("agent_failed run_id=%s agent=%s", state.run_id, name.value)
            result = AgentResult(agent_name=name, status="error", errors=["AGENT_EXECUTION_FAILED"])
        state.agent_results[name] = result
        state.errors.extend(result.errors)
        state.trace.append(TraceEvent(agent_name=name, status=result.status))
        logger.info("agent_result run_id=%s agent=%s status=%s", state.run_id, name.value, result.status)
        return result
