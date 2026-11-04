"""Persist serving metadata and complete versioned run snapshots."""
from alembic import op
import sqlalchemy as sa
revision='0002_phase03'
down_revision='0001_phase02'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('workflow_runs',sa.Column('response',sa.JSON(),nullable=True))
    op.add_column('predictions',sa.Column('result',sa.JSON(),nullable=True))
    op.add_column('agent_events',sa.Column('event',sa.JSON(),nullable=True))

def downgrade():
    op.drop_column('agent_events','event'); op.drop_column('predictions','result'); op.drop_column('workflow_runs','response')
