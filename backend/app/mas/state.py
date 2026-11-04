"""v1 aliases retained; v2 transitions are validated before every mutation."""
from backend.app.schemas.contracts import WorkflowState, TraceEvent
from backend.app.schemas.runtime import (WorkflowState as RuntimeState, TraceEvent as RuntimeTrace,
    WorkflowStatus, AgentStatus, AgentResult)
from backend.app.schemas.contracts import AgentName
from uuid import UUID

AGENT_TRANSITIONS = {
    AgentStatus.NOT_STARTED: {AgentStatus.RUNNING, AgentStatus.SKIPPED, AgentStatus.UNAVAILABLE},
    AgentStatus.RUNNING: {AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.UNAVAILABLE},
}

def record(state: RuntimeState, status: str, reason: str, agent_id: AgentName | None = None,
           message_id: UUID | None = None):
    state.trace.append(RuntimeTrace(sequence=len(state.trace)+1, run_id=state.run_id,
        agent_id=agent_id, message_id=message_id, status=status, reason=reason))

def transition_agent(state: RuntimeState, result: AgentResult, reason: str, message_id: UUID | None = None, safety_stage: str | None = None):
    previous = state.agent_results[result.agent_id].status
    output_recheck = (result.agent_id == AgentName.safety and safety_stage == 'output'
        and result.status == AgentStatus.RUNNING and previous in {AgentStatus.COMPLETED,AgentStatus.FAILED,AgentStatus.UNAVAILABLE}
        and any(d.stage == 'input' for d in state.safety_decisions)
        and not any(d.stage == 'output' for d in state.safety_decisions))
    if not output_recheck and result.status not in AGENT_TRANSITIONS.get(previous, set()):
        raise ValueError(f"Illegal agent transition: {previous} -> {result.status}")
    state.agent_results[result.agent_id] = result
    record(state, result.status.value, reason, result.agent_id, message_id)

def transition_workflow(state: RuntimeState, status: WorkflowStatus):
    if state.status == WorkflowStatus.NOT_STARTED:
        allowed = {WorkflowStatus.RUNNING}
    elif state.status == WorkflowStatus.RUNNING:
        allowed = {WorkflowStatus.COMPLETED, WorkflowStatus.DEGRADED, WorkflowStatus.BLOCKED, WorkflowStatus.FAILED}
    else:
        allowed = set()
    if status not in allowed:
        raise ValueError(f"Illegal workflow transition: {state.status} -> {status}")
    state.status = status
    record(state, status.value, "WORKFLOW_TRANSITION")
