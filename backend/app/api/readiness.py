"""Dependency probes, separate from liveness. No credentials or raw errors exposed."""
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter(prefix='/api/v1/system', tags=['system'])


@router.get('/readiness')
def readiness(request: Request):
    state = request.app.state
    components = {'backend': {'status': 'available'}, 'coordinator': {'status': 'available'},
                  'safety': {'status': 'available', 'version': 'safety-1.1'}}
    for name, probe in [('postgresql', lambda: probe_db(state)),
                        ('neo4j', lambda: state.knowledge_store.summary()),
                        ('model', lambda: probe_model(state)),
                        ('rl_policy', lambda: probe_policy(state))]:
        try:
            detail = probe()
            components[name] = {'status': 'available', **detail}
        except Exception:
            components[name] = {'status': 'unavailable', 'code': name.upper() + '_UNAVAILABLE'}
    return {'phase': '07', 'checked_at': datetime.now(timezone.utc).isoformat(),
            'components': components, 'scope': 'Dependency connectivity/artifact checks; not clinical validation'}


def probe_db(state):
    with state.db_engine.connect() as connection:
        if connection.scalar(text('SELECT version_num FROM alembic_version')) != '0002_phase03':
            raise ValueError('Migration mismatch')
        connection.execute(text('SELECT response FROM workflow_runs LIMIT 0'))
    return {'storage': 'PostgreSQL', 'migration': '0002_phase03'}


def probe_model(state):
    state.model_service.load()
    return {'version': state.model_service.version}


def probe_policy(state):
    state.policy_service.load()
    return {'version': state.policy_service.manifest.policy_version, 'scope': 'synthetic simulator'}
