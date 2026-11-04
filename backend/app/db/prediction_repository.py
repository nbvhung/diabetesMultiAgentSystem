"""Caller-owned transaction: no commit here; no raw features in logs."""
from uuid import uuid4
from datetime import datetime,timezone
from sqlalchemy import MetaData,Table,select,insert,update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from backend.app.schemas.runtime import WorkflowResponse

class PredictionRepository:
    def __init__(self,connection):
        self.connection=connection
        metadata=MetaData()
        for name in ['demo_cases','assessments','model_versions','predictions','workflow_runs','agent_events']:
            setattr(self,name,Table(name,metadata,autoload_with=connection))

    def ensure_run(self,run_id):
        self.connection.execute(pg_insert(self.workflow_runs).values(id=run_id,status='RUNNING',schema_version='2.4').on_conflict_do_nothing(index_elements=['id']))

    def persist_prediction(self,run_id,assessment,result,service):
        self.ensure_run(run_id)
        model_id=uuid4()
        self.connection.execute(pg_insert(self.model_versions).values(id=model_id,version=result.model_version,artifact_uri=service.path.as_uri(),sha256=service.digest).on_conflict_do_nothing(index_elements=['version']))
        model=self.connection.execute(select(self.model_versions).where(self.model_versions.c.version==result.model_version)).mappings().one()
        if model['sha256']!=service.digest: raise ValueError('REGISTERED_MODEL_DIGEST_MISMATCH')
        case_id,assessment_id,prediction_id=uuid4(),uuid4(),uuid4()
        self.connection.execute(insert(self.demo_cases).values(id=case_id,label='SYNTHETIC_INFERENCE_CASE',is_synthetic=True))
        self.connection.execute(insert(self.assessments).values(id=assessment_id,demo_case_id=case_id,features=assessment.model_dump(mode='json'),schema_version='1.0'))
        result=result.model_copy(update={'persisted_record_id':prediction_id})
        self.connection.execute(insert(self.predictions).values(id=prediction_id,assessment_id=assessment_id,model_version_id=model['id'],workflow_run_id=run_id,score=result.score,predicted_class=result.predicted_class,result=result.model_dump(mode='json')))
        return result

    def save(self,run):
        self.ensure_run(run.run_id)
        self.connection.execute(update(self.workflow_runs).where(self.workflow_runs.c.id==run.run_id).values(status=run.status.value,finished_at=datetime.now(timezone.utc),response=run.model_dump(mode='json')))
        for event in run.agent_trace:
            self.connection.execute(insert(self.agent_events).values(id=uuid4(),workflow_run_id=run.run_id,sequence=event.sequence,agent_id=event.agent_id.value if event.agent_id else 'coordinator',status=event.status.value,message_id=event.message_id,event=event.model_dump(mode='json')))

class LegacyRunRequiresReview(Exception): pass

class PostgresRunRepository:
    def __init__(self,engine): self.engine=engine
    def get(self,run_id):
        with self.engine.connect() as conn:
            table=Table('workflow_runs',MetaData(),autoload_with=conn)
            data=conn.scalar(select(table.c.response).where(table.c.id==run_id))
            if data and data.get('schema_version') != '2.4': raise LegacyRunRequiresReview()
            return WorkflowResponse.model_validate(data) if data else None
