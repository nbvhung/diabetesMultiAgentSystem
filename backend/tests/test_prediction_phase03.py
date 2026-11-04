"""SYNTHETIC only. PostgreSQL integration requires dedicated database."""
import json, os, shutil
from uuid import uuid4
import pytest
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,text
from backend.app.ml.serving import ModelService,ModelUnavailable
from backend.app.ml.pipeline import ART, FEATURES,sha
from backend.app.schemas.contracts import AssessmentInput,AgentName
from backend.app.main import create_app
from backend.app.db.prediction_repository import PostgresRunRepository

SYNTHETIC=dict(pregnancies=0,glucose=100,blood_pressure=70,skin_thickness=20,insulin=50,bmi=22,diabetes_pedigree=0.3,age=30)

def test_serving_checkpoint_feature_order_determinism():
    service=ModelService(); assessment=AssessmentInput(**SYNTHETIC)
    a=service.predict(assessment); model=service.model
    b=service.predict(AssessmentInput(**dict(reversed(list(SYNTHETIC.items())))))
    assert a.score==b.score and service.model is model and not model.training
    assert a.model_version=='pima-mlp-0.2.0' and a.preprocessing_version.startswith('sha256:')
    assert a.inference_latency_ms>=0 and list(service.pipe.feature_names_in_)==FEATURES
    stats=service.pipe['imputer'].statistics_.copy()
    result=service.predict(AssessmentInput(**(SYNTHETIC|{'age':120,'insulin':0})))
    assert 'OUTSIDE_TRAINING_RANGE:age' in result.warnings
    assert 'ZERO_TREATED_AS_MISSING:insulin' in result.warnings
    np.testing.assert_array_equal(stats,service.pipe['imputer'].statistics_)

@pytest.mark.parametrize('mode',['missing','corrupt','version','schema'])
def test_model_unavailable(tmp_path,mode):
    folder=tmp_path/'artifact'; shutil.copytree(ART,folder)
    if mode=='missing': (folder/'checkpoint.pt').unlink()
    elif mode=='corrupt': (folder/'checkpoint.pt').write_bytes(b'bad checkpoint')
    elif mode=='schema':
        data=json.loads((folder/'serving.json').read_text()); data['features']=list(reversed(FEATURES)); (folder/'serving.json').write_text(json.dumps(data))
    service=ModelService(folder,expected_version='wrong' if mode=='version' else 'pima-mlp-0.2.0')
    with pytest.raises(ModelUnavailable): service.load()
    assert not service._loaded

@pytest.fixture
def db_engine():
    url=os.getenv('PHASE03_TEST_DATABASE_URL')
    if not url: pytest.skip('Dedicated PHASE03_TEST_DATABASE_URL required')
    from alembic.config import Config
    from alembic import command
    from backend.app.core.config import settings
    from backend.app.db import session
    engine=create_engine(url,hide_parameters=True)
    old_url,old_engine=settings.database_url,session.engine
    settings.database_url=url; session.engine=engine
    try: command.upgrade(Config('alembic.ini'),'head')
    finally: settings.database_url=old_url; session.engine=old_engine
    yield engine
    engine.dispose()

def test_api_integration_persistence_restart_and_validation(db_engine):
    app=create_app(prediction_enabled=True,engine=db_engine)
    with TestClient(app) as client:
        assert client.get('/api/v1/models/current').status_code==200
        body={'assessment':SYNTHETIC,'is_synthetic':True}
        response=client.post('/api/v1/mas/runs',json=body)
        assert response.status_code==201,response.text
        run=response.json(); result=run['agent_results']['prediction']
        assert result['status']=='COMPLETED' and result['implementation']=='integrated'
        pred=result['output']; assert pred['schema_version']=='1.1' and pred['persisted_record_id']
        assert any(e['model_version']==pred['model_version'] for e in run['agent_trace'])
        assert client.get('/api/v1/mas/runs/'+run['run_id']).json()==run
        assert client.get('/api/v1/mas/runs/'+run['run_id']+'/trace').json()['agent_trace']==run['agent_trace']
        assert PostgresRunRepository(db_engine).get(run['run_id']).agent_results[AgentName.prediction].output.score==pred['score']
        with db_engine.connect() as conn:
            assert conn.scalar(text('SELECT count(*) FROM predictions WHERE workflow_run_id=:id'),{'id':run['run_id']})==1
            assert conn.scalar(text('SELECT count(*) FROM agent_events WHERE workflow_run_id=:id'),{'id':run['run_id']})==len(run['agent_trace'])
            before=conn.scalar(text('SELECT count(*) FROM predictions'))
        for invalid in [dict(SYNTHETIC,glucose=-1),dict(SYNTHETIC,glucose='100'),{'age':30}]:
            assert client.post('/api/v1/mas/runs',json={'assessment':invalid,'is_synthetic':True}).status_code==422
        assert client.post('/api/v1/mas/runs',json={'assessment':SYNTHETIC}).status_code==422
        question=client.post('/api/v1/mas/runs',json={'question':'Synthetic education question'}).json()
        assert question['agent_results']['prediction']['status']=='SKIPPED'
        with db_engine.connect() as conn: assert conn.scalar(text('SELECT count(*) FROM predictions'))==before

def test_database_failure_rolls_back(db_engine,monkeypatch):
    from backend.app.db.prediction_repository import PredictionRepository
    with db_engine.connect() as c:
        before={t:c.scalar(text('SELECT count(*) FROM '+t)) for t in ['assessments','predictions','workflow_runs','demo_cases','model_versions','agent_events']}
    original=PredictionRepository.persist_prediction
    def broken(self,*args):
        original(self,*args)
        raise RuntimeError('SENSITIVE_ERROR_DO_NOT_LOG')
    monkeypatch.setattr(PredictionRepository,'persist_prediction',broken)
    with TestClient(create_app(prediction_enabled=True,engine=db_engine)) as client:
        response=client.post('/api/v1/mas/runs',json={'assessment':SYNTHETIC,'is_synthetic':True})
        assert response.status_code==503 and 'SENSITIVE_ERROR' not in response.text
    with db_engine.connect() as c:
        assert {t:c.scalar(text('SELECT count(*) FROM '+t)) for t in before}==before

def test_missing_model_never_predicts(db_engine,tmp_path):
    app=create_app(prediction_enabled=True,engine=db_engine,model_service=ModelService(tmp_path))
    with TestClient(app) as client:
        assert client.get('/api/v1/models/current').status_code==503
        response=client.post('/api/v1/mas/runs',json={'assessment':SYNTHETIC,'is_synthetic':True})
        assert response.status_code==201
        assert response.json()['agent_results']['prediction']['status']=='UNAVAILABLE'
        assert response.json()['agent_results']['prediction']['output'] is None


def test_prediction_result_in_workflow_state(db_engine):
    import asyncio
    from backend.app.mas.coordinator import Coordinator
    from backend.app.mas.registry import AgentRegistry
    from backend.app.mas.agents.prediction import PredictionAgent
    from backend.app.db.prediction_repository import PredictionRepository
    from backend.app.schemas.runtime import WorkflowState,RunInput,AgentResult,AgentStatus,PredictionTask,SafetyTask
    from backend.app.mas.agents.safety import SafetyAgent
    with db_engine.connect() as connection:
        tx=connection.begin()
        try:
            registry=AgentRegistry(); registry.register(PredictionAgent(ModelService(),PredictionRepository(connection)))
            state=WorkflowState(request=RunInput(assessment=AssessmentInput(**SYNTHETIC),is_synthetic=True))
            from backend.app.mas.state import transition_workflow
            from backend.app.schemas.runtime import WorkflowStatus
            transition_workflow(state,WorkflowStatus.RUNNING)
            registry.register(SafetyAgent())
            state.agent_results[AgentName.safety]=AgentResult(agent_id=AgentName.safety,status=AgentStatus.NOT_STARTED,implementation='integrated')
            coordinator=Coordinator(registry,persistent=True)
            asyncio.run(coordinator.check_safety(state,SafetyTask(stage='input',assessment=SYNTHETIC)))
            state.agent_results[AgentName.prediction]=AgentResult(agent_id=AgentName.prediction,status=AgentStatus.NOT_STARTED,implementation='integrated')
            result=asyncio.run(Coordinator(registry,persistent=True).dispatch(state,AgentName.prediction,PredictionTask(assessment=state.request.assessment)))
            assert state.agent_results[AgentName.prediction]==result and result.output.persisted_record_id
            assert state.trace[-1].model_version==result.output.model_version
        finally: tx.rollback()

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1])
def test_nonfinite_negative_input(value):
    from pydantic import ValidationError
    with pytest.raises(ValidationError): AssessmentInput(**(SYNTHETIC|{'glucose':value}))
