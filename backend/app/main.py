import logging
from threading import RLock
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.api.system import router
from backend.app.api.mas import router as mas_router
from backend.app.core.config import settings
from backend.app.mas.registry import build_runtime_registry
from backend.app.mas.repository import InMemoryRunRepository, RunRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

def create_app(repository: RunRepository | None = None, registry_factory=build_runtime_registry, *, prediction_enabled=True, engine=None, model_service=None, knowledge_store=None, policy_service=None, research_services=None) -> FastAPI:
    application = FastAPI(title="Diabetes MAS - Grounded Research Workspace", version="0.7.1")
    application.state.research_services=research_services
    application.state.research_lock=RLock()
    application.state.run_repository = repository if repository is not None else InMemoryRunRepository()
    application.state.registry_factory = registry_factory
    application.state.prediction_enabled = prediction_enabled
    from backend.app.rl.policy import PolicyService
    application.state.policy_service = policy_service if policy_service is not None else PolicyService()
    from backend.app.knowledge.store import GraphStore
    application.state.knowledge_store = knowledge_store if knowledge_store is not None else (GraphStore() if prediction_enabled else None)
    if prediction_enabled:
        from sqlalchemy import create_engine
        from backend.app.ml.serving import ModelService
        from backend.app.db.prediction_repository import PostgresRunRepository
        application.state.db_engine = engine if engine is not None else create_engine(settings.database_url, hide_parameters=True, pool_pre_ping=True, connect_args={'connect_timeout':5,'options':'-c statement_timeout=10000'})
        application.state.model_service = model_service if model_service is not None else ModelService(device=__import__('os').getenv('MODEL_DEVICE','cpu'))
        application.state.run_repository = PostgresRunRepository(application.state.db_engine)
    application.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
        allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
    application.include_router(router)
    application.include_router(mas_router)
    from backend.app.api.knowledge import router as knowledge_router
    application.include_router(knowledge_router)
    from backend.app.api.readiness import router as readiness_router
    from backend.app.api.experiments import router as experiments_router
    application.include_router(readiness_router)
    application.include_router(experiments_router)
    from backend.app.research.api import router as research_router
    application.include_router(research_router)

    @application.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        logging.getLogger(__name__).error("Unhandled application error type=%s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"error": "INTERNAL_SERVER_ERROR"})

    return application

app = create_app(prediction_enabled=True)
