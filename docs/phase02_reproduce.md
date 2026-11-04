# Phase 02 reproduction — PowerShell

Run from diabetes-mas-final. Existing MAS contracts and Coordinator are unchanged. Models are offline research artifacts only; Prediction Agent stays stub until Phase 03.

```powershell
python -m pip install -e ".[dev,ml]"
python scripts/download_pima.py
# Dedicated disposable PostgreSQL DB ONLY: tests perform downgrade/upgrade.
$env:PHASE02_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_phase02_test'
python scripts/run_phase02.py
```

Supply actual credentials through environment, never source. Without PHASE02_TEST_DATABASE_URL the PostgreSQL integration test SKIPS and cannot establish Phase 02 PASS. run_phase02 executes all three notebooks in order via nbconvert with timeout 600 seconds/cell, then all backend tests. Examine log for skips, not merely command exit code.

Direct notebook execution:

```powershell
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_diabetes_eda_and_split.ipynb notebooks/02_diabetes_dl_training.ipynb notebooks/03_diabetes_model_evaluation.ipynb --ExecutePreprocessor.timeout=600
```

Application DB migration (not runtime run persistence integration):

```powershell
$env:DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_mas'
python -m alembic upgrade head
python -m alembic current
```

Migration creates demo_cases, assessments, model_versions, predictions, workflow_runs, agent_events with UUID PKs, timezone timestamps, FK indexes, unique event sequence, synthetic-only demo constraint, score/class constraints. Assessments reference synthetic demo cases only. Features are versioned JSON, validated by Pydantic when later application integration is built; DB does not enforce JSON feature keys. No training rows or demo seeds inserted. No runtime repository integration in Phase 02. Alembic explicit migration is source of schema truth; ORM models/autogeneration not yet implemented.

Actual local verification uses an isolated PostgreSQL 17 cluster under D:\TEMP, loopback port 55432, test DB diabetes_phase02_test, user phase02_local. Authentication trust is limited to this temporary local cluster, stopped after tests; not a deployment example. Existing installed service/data is untouched. On another machine use your own disposable PostgreSQL database as above.

Artifacts: artifacts/models/pima-mlp-0.2.0/checkpoint.pt, preprocessing.joblib, manifest.json, training_config.json, preprocessing_config.json. Manifest pins each artifact digest and environment; load_checkpoint validates all listed files before weights_only=True torch.load. Joblib is pickle-based: only load trusted local artifacts; checksum detects changes, not attacker authenticity. Figures in experiments/figures/phase02; results and split indices in experiments/results/phase02. Exact dependency versions in environment.json; cross-platform bitwise equivalence is not promised.
