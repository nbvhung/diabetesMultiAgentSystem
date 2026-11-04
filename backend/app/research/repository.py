"""Same transaction/schema, separate explicit wire version. No historical relabeling."""
from sqlalchemy import select,Table,MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert
from backend.app.db.prediction_repository import PredictionRepository,LegacyRunRequiresReview
from backend.app.schemas.runtime import WorkflowResponse as HistoricalResponse
from .schemas import WorkflowResponse


class ResearchRepository(PredictionRepository):
    def ensure_run(self,run_id):
        self.connection.execute(pg_insert(self.workflow_runs).values(id=run_id,status='RUNNING',schema_version='3.0').on_conflict_do_nothing(index_elements=['id']))


def get_run(engine,run_id):
    with engine.connect() as conn:
        table=Table('workflow_runs',MetaData(),autoload_with=conn)
        data=conn.scalar(select(table.c.response).where(table.c.id==run_id))
    if not data:return None
    if data.get('schema_version')=='3.0':return WorkflowResponse.model_validate(data)
    if data.get('schema_version')=='2.4':return HistoricalResponse.model_validate(data)
    raise LegacyRunRequiresReview()
