from uuid import UUID
from fastapi import APIRouter, Request, HTTPException
from backend.app.mas.coordinator import Coordinator
from backend.app.schemas.runtime import RunInput, WorkflowResponse

router = APIRouter(prefix="/api/v1/mas", tags=["mas"])

@router.post("/runs", response_model=WorkflowResponse, status_code=201)
async def create_run(payload: RunInput, request: Request):
    if request.app.state.prediction_enabled:
        from pydantic import ValidationError
        from backend.app.schemas.contracts import AssessmentInput, AgentName
        from backend.app.schemas.runtime import AgentStatus
        from backend.app.db.prediction_repository import PredictionRepository
        if payload.assessment is not None:
            if payload.is_synthetic is not True:
                raise HTTPException(422, 'SYNTHETIC_CONFIRMATION_REQUIRED')
            try:
                AssessmentInput.model_validate((await request.json())['assessment'], strict=True)
            except ValidationError:
                raise HTTPException(422, 'INVALID_ASSESSMENT_TYPES') from None
        try:
            with request.app.state.db_engine.begin() as connection:
                repository = PredictionRepository(connection)
                result = await Coordinator(integrated_registry(request, repository), persistent=True).run(payload)
                if result.agent_results[AgentName.prediction].status == AgentStatus.FAILED:
                    raise HTTPException(503, 'PREDICTION_TRANSACTION_FAILED')
                repository.save(result)
            return result
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, 'PERSISTENCE_UNAVAILABLE') from None
    coordinator = Coordinator(request.app.state.registry_factory())
    result = await coordinator.run(payload)
    request.app.state.run_repository.save(result)
    return result

@router.get("/runs/{run_id}", response_model=WorkflowResponse)
def get_run(run_id: UUID, request: Request):
    try:
        result = request.app.state.run_repository.get(run_id)
    except Exception as exc:
        from backend.app.db.prediction_repository import LegacyRunRequiresReview
        if isinstance(exc,LegacyRunRequiresReview): raise HTTPException(409,'LEGACY_RUN_REQUIRES_SAFETY_REVIEW') from None
        raise HTTPException(503, 'PERSISTENCE_UNAVAILABLE') from None
    if result is None:
        raise HTTPException(status_code=404, detail="RUN_NOT_FOUND_OR_EVICTED")
    return result

@router.get("/runs/{run_id}/trace")
def get_trace(run_id: UUID, request: Request):
    result = get_run(run_id, request)
    return {"schema_version": "2.4", "run_id": result.run_id, "agent_trace": result.agent_trace}

@router.get("/agents")
def get_agents(request: Request):
    return {"schema_version": "2.4", "agents": [{
        "agent_id": spec.agent_id, "description": spec.description,
        "input_schema": spec.input_schema.model_json_schema(),
        "output_schema": spec.output_schema.model_json_schema(),
        "permitted_tools": spec.permitted_tools, "implementation": spec.implementation,
        "available": spec.available, "timeout_seconds": spec.timeout_seconds,
        "fallback_policy": spec.fallback_policy, "status_semantics": spec.status_semantics,
    } for spec in (integrated_registry(request).definitions() if request.app.state.prediction_enabled else request.app.state.registry_factory().definitions())]}


def integrated_registry(request, repository=None):
    from backend.app.mas.registry import AgentRegistry
    from backend.app.mas.agents.prediction import PredictionAgent
    from backend.app.mas.agents.rl_decision import RLDecisionAgent
    from backend.app.mas.agents.safety import SafetyAgent
    from backend.app.mas.agents.knowledge import KnowledgeAgent, EducationAgent
    from backend.app.rag.retrieval import Retrieval
    registry=AgentRegistry()
    for agent in (PredictionAgent(request.app.state.model_service, repository),KnowledgeAgent(Retrieval(request.app.state.knowledge_store)),RLDecisionAgent(request.app.state.policy_service),EducationAgent(),SafetyAgent()):
        registry.register(agent)
    return registry

