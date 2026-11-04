import json, os
import numpy as np
import pytest
import torch
import joblib
from backend.app.ml.pipeline import *

def test_dataset_schema():
    df=load_data(); assert df.shape==(768,9)
    with pytest.raises(ValueError): validate_data(df.iloc[:-1])
    bad=df.copy(); bad.loc[0,'Outcome']=3
    with pytest.raises(ValueError): validate_data(bad)

def test_split_reproducibility_and_no_leakage():
    df=load_data(); splits=split_indices(df)
    assert splits==split_indices(df)==json.loads((RES/'splits.json').read_text())
    a,b,c=map(set,[splits['train'],splits['validation'],splits['test']])
    assert not a&b and not a&c and not b&c and a|b|c==set(range(768))
    for idx in splits.values(): assert abs(df.Outcome.iloc[idx].mean()-df.Outcome.mean())<0.02
    pipe=joblib.load(ART/'preprocessing.joblib')
    train=features(df).iloc[splits['train']]
    np.testing.assert_allclose(pipe['imputer'].statistics_,train.median().to_numpy())
    np.testing.assert_allclose(pipe['scaler'].mean_,pipe['imputer'].transform(train).mean(axis=0))

def test_transform_consistency_and_shape():
    data=arrays(); model=load_checkpoint(); pipe=joblib.load(ART/'preprocessing.joblib')
    df=load_data(); idx=json.loads((RES/'splits.json').read_text())['test']
    np.testing.assert_allclose(data['test'][0],pipe.transform(features(df).iloc[idx]).astype('float32'))
    x=torch.from_numpy(data['test'][0])
    with torch.no_grad(): out=model(x)
    assert out.shape==(len(idx),) and torch.isfinite(out).all()
    assert all(0<=v<=1 for row in json.loads((RES/'metrics.json').read_text()).values() for v in row.values())

def test_notebooks_executed_without_error():
    import nbformat
    for p in (ROOT/'notebooks').glob('*diabetes*.ipynb'):
        nb=nbformat.read(p,as_version=4)
        cells=[c for c in nb.cells if c.cell_type=='code']
        assert cells and all(c.execution_count is not None for c in cells)
        assert not any(o.output_type=='error' for c in cells for o in c.outputs)

def test_postgres_migration():
    from sqlalchemy import create_engine,inspect,text
    from alembic.config import Config
    from alembic import command
    url=os.getenv('PHASE02_TEST_DATABASE_URL')
    if not url: pytest.skip('Set PHASE02_TEST_DATABASE_URL to a dedicated empty PostgreSQL database')
    # Caller must use dedicated test database: upgrade/downgrade are destructive there.
    from backend.app.core.config import settings
    from backend.app.db import session
    original=settings.database_url; old_engine=session.engine
    engine=create_engine(url)
    settings.database_url=url; session.engine=engine
    try:
        cfg=Config(str(ROOT/'alembic.ini')); command.upgrade(cfg,'head')
        names=set(inspect(engine).get_table_names())
        assert {'demo_cases','assessments','model_versions','predictions','workflow_runs','agent_events'}<=names
        with engine.connect() as c:
            assert c.scalar(text('SELECT version_num FROM alembic_version'))=='0002_phase03'
        command.downgrade(cfg,'base')
        assert 'demo_cases' not in inspect(engine).get_table_names()
        command.upgrade(cfg,'head')
    finally:
        settings.database_url=original; session.engine=old_engine; engine.dispose()
