from fastapi import APIRouter, Request, HTTPException
router = APIRouter()

@router.get("/health")
def health(request: Request):
    return {"status": "ok", "phase": "07" if request.app.state.prediction_enabled else "01", "scope": "application_liveness"}

@router.get("/api/v1/system/capabilities")
def capabilities(request: Request):
    if request.app.state.prediction_enabled:
        from backend.app.api.readiness import readiness
        status=readiness(request)['components']
        model=status['model']['status']; graph=status['neo4j']['status']; policy=status['rl_policy']['status']
        return {"schema_version":"1.0","phase":"07","components":{"api":"available","coordinator":"available","prediction_agent":model,"deep_learning":model,"database":status['postgresql']['status'],"neo4j_rag":graph,"knowledge_agent":graph,"rl_policy":policy,"rl_agent":"available","education_agent":"available","safety_agent":"available","rules":"available"},"note":"Actual dependency probes; RL agent supports explicit rule fallback when trained policy is unavailable. See /api/v1/system/readiness for versions and probe time. Research only."}
    return {"schema_version": "1.0", "phase": "01", "components": {
        "api": "available", "coordinator": "available", "database": "unavailable",
        "deep_learning": "stub", "neo4j_rag": "stub", "rules": "available", "rl_policy": "stub",
        "prediction_agent": "stub", "knowledge_agent": "stub", "rl_agent": "stub",
        "education_agent": "available", "safety_agent": "available", "run_storage": "available",
    }, "note": "Education is abstention-only; safety uses the versioned mandatory two-gate policy. Models/RAG/policy are NOT integrated. Storage is bounded process-local RAM; database connectivity is unverified."}


@router.get('/api/v1/models/current')
def current_model(request: Request):
    if not request.app.state.prediction_enabled:
        raise HTTPException(503,'PREDICTION_NOT_ENABLED')
    from backend.app.ml.serving import ModelUnavailable
    service=request.app.state.model_service
    try: service.load()
    except ModelUnavailable: raise HTTPException(503,'MODEL_UNAVAILABLE') from None
    return {'model_id':'pima-mlp','model_version':service.version,'preprocessing_version':service.preprocessing_version,'device':service.device,'features':list(service.bounds),'limitations':['Research score only; not calibrated clinical probability or diagnosis.']}
