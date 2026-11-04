# Phase 02 validation — PASS, READY_FOR_PHASE_03

Generated UTC: 2026-11-01T20:21:12.943588+00:00. Scope: Phase 02 only. No Coordinator or agent contract modifications. Prediction Agent remains unavailable stub; model is offline, not clinical diagnosis.

## Commands and actual evidence

- Dataset fetched with Invoke-WebRequest from verified jbrownlee CSV mirror after sandbox network denial; escalation succeeded. No synthetic training data substituted. SHA256 pinned in downloader/data card.
- `python scripts/run_phase02.py` with PHASE02_TEST_DATABASE_URL pointing to isolated local test DB: exit 0. Executes three notebooks via nbconvert in place and runs pytest. [results.json](results.json), [notebooks.log](notebooks.log), [pytest.log](pytest.log).
- `python -m pytest backend/tests -v`: **53 passed, 0 skipped, 4 warnings**. Includes dataset validation, disjoint/reproducible split, train-only imputer/scaler stats, transform consistency, checkpoint checksum/load/output shape, executed notebook checks, PostgreSQL migration and all 48 previous tests.
- PostgreSQL 17 installed binary used to init separate cluster D:/TEMP/diabetes-mas-phase02-20261102, loopback 55432, database diabetes_phase02_test, local test user phase02_local. Existing service/data untouched. Test runs Alembic upgrade head, inspects six tables/revision, downgrade base, verifies removal, upgrade head again. Cluster stopped successfully using pg_ctl after checks. No raw records inserted.
- Notebook execution first PowerShell redirection reported shell exit 1 from native stderr warnings despite completed cells. Re-ran with subprocess capture: nbconvert exit 0, all code cells executed/no errors. Official evidence is the rerun.
- Initial initdb in sandbox failed restricted token and Unicode path; isolated ASCII temporary cluster with approved escalation succeeded. No existing DB credentials were read or secrets committed.

## Real model results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC (AP) | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| MLP | 0.758621 | 0.709677 | 0.536585 | 0.611111 | 0.863415 | 0.781957 | 0.151729 |
| LogisticRegression | 0.775862 | 0.777778 | 0.512195 | 0.617647 | 0.862439 | 0.783225 | 0.149270 |
| RandomForest | 0.732759 | 0.666667 | 0.487805 | 0.563380 | 0.827967 | 0.757576 | 0.161513 |

44 epochs executed; selected epoch 24, minimum validation loss. Held-out test n=116; positive n=41. Split train=537/validation=115/test=116 with indices in experiments/results/phase02/splits.json. Zero-as-missing rules applied before train-only median/scaling. Threshold 0.5 fixed. No test used for early stopping or fitting. AP is average precision; Brier and reliability diagrams assess uncalibrated scores, no clinical calibration claim.

## Deliverables

- notebooks/01_diabetes_eda_and_split.ipynb, 02_diabetes_dl_training.ipynb, 03_diabetes_model_evaluation.ipynb — executed with stored outputs/counts.
- backend/app/ml/pipeline.py — validation/split/preprocessing/MLP/checksum/training/evaluation helpers. Training and evaluation loops also visible in corresponding notebook cells.
- artifacts/models/pima-mlp-0.2.0/ — checkpoint.pt, preprocessing.joblib, configs and manifest (actual files, gitignored).
- experiments/results/phase02/metrics.csv/json, splits and summaries/history/environment; experiments/figures/phase02/ — 6 PNGs generated from actual data/run.
- backend/app/db/migrations/versions/0001_phase02.py — six tables, FK/index/timestamps and constraints. No runtime DB persistence integration or seeded patients.
- backend/tests/test_ml_phase02.py; scripts/download_pima.py; scripts/run_phase02.py.
- docs/data_card.md, docs/model_card.md, docs/phase02_reproduce.md; README, AGENTS, phase_status and pyproject updated. Existing v1/v2 MAS schemas and Coordinator unchanged.

## Limitations

Mirror license unverified, no invented license; cohort-specific historical data, small test set, no external validation/fairness/clinical utility evidence. All source links/provenance in data card. LR outperformed MLP accuracy/F1 here; no forced DL superiority. Raw data/artifacts ignored, public training data not inserted as demo patients. Demo_cases enforces synthetic=true. No real patient demo data generated.

Database features JSON validation is application responsibility in future integration; no ORM/autogeneration or persistent MAS repository added. Dedicated migration test does not test production deployment. Tests with no dedicated DB environment skip migration and must not be treated as proof of Phase 02 PASS.

Warnings: TestClient/httpx deprecation and Alembic prepend_sys_path legacy warning. Notebook kernel emitted local permission/TCP warnings; execution completed, no cell errors. No new frontend functionality/build changes required in this phase. Reproduction requires installed .[dev,ml] dependencies and PostgreSQL.

Git not initialized from previous phases; no commit/push or commit hash. No Phase 03 work performed.
