"""Phase 02 minimal research schema; no real-patient records allowed."""
from alembic import op
import sqlalchemy as sa
revision='0001_phase02'
down_revision=None
branch_labels=None
depends_on=None

def stamp(): return sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now())
def identity(): return sa.Column('id',sa.Uuid(),primary_key=True)
def upgrade():
    op.create_table('demo_cases',identity(),sa.Column('label',sa.String(200),nullable=False),sa.Column('is_synthetic',sa.Boolean(),nullable=False,server_default=sa.true()),stamp(),sa.CheckConstraint('is_synthetic = true',name='ck_demo_synthetic'))
    op.create_table('assessments',identity(),sa.Column('demo_case_id',sa.Uuid(),sa.ForeignKey('demo_cases.id'),nullable=False),sa.Column('features',sa.JSON(),nullable=False),sa.Column('schema_version',sa.String(20),nullable=False),stamp())
    op.create_table('model_versions',identity(),sa.Column('version',sa.String(100),nullable=False,unique=True),sa.Column('artifact_uri',sa.Text(),nullable=False),sa.Column('sha256',sa.String(64),nullable=False),stamp())
    op.create_table('workflow_runs',identity(),sa.Column('status',sa.String(30),nullable=False),sa.Column('schema_version',sa.String(20),nullable=False),sa.Column('finished_at',sa.DateTime(timezone=True)),stamp())
    op.create_table('predictions',identity(),sa.Column('assessment_id',sa.Uuid(),sa.ForeignKey('assessments.id'),nullable=False),sa.Column('model_version_id',sa.Uuid(),sa.ForeignKey('model_versions.id'),nullable=False),sa.Column('workflow_run_id',sa.Uuid(),sa.ForeignKey('workflow_runs.id')),sa.Column('score',sa.Float(),nullable=False),sa.Column('predicted_class',sa.Integer(),nullable=False),stamp(),sa.CheckConstraint('score >= 0 AND score <= 1',name='ck_score'),sa.CheckConstraint('predicted_class IN (0,1)',name='ck_class'))
    op.create_table('agent_events',identity(),sa.Column('workflow_run_id',sa.Uuid(),sa.ForeignKey('workflow_runs.id'),nullable=False),sa.Column('sequence',sa.Integer(),nullable=False),sa.Column('agent_id',sa.String(50),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('message_id',sa.Uuid()),stamp(),sa.UniqueConstraint('workflow_run_id','sequence',name='uq_event_sequence'))
    for table,cols in [('assessments',['demo_case_id']),('predictions',['assessment_id']),('predictions',['model_version_id']),('predictions',['workflow_run_id']),('agent_events',['workflow_run_id']),('workflow_runs',['created_at'])]:
        op.create_index('ix_'+table+'_'+'_'.join(cols),table,cols)

def downgrade():
    for table in ['agent_events','predictions','workflow_runs','model_versions','assessments','demo_cases']: op.drop_table(table)
