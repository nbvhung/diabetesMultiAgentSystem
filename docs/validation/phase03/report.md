# Phase 03 — PASS, READY_FOR_PHASE_04

Report UTC: 2026-11-01T20:32:46.547053+00:00. Scope only Phase 03. Knowledge/Neo4j/RAG/RL remain stubs, no training or Phase 04 implementation.

## Actual commands and evidence

- Started only prior dedicated PostgreSQL 17 temporary cluster on 127.0.0.1:55432 via pg_ctl. Existing installed service/databases untouched. Created diabetes_phase03_test separately from diabetes_phase02_test; no credentials or raw clinical profiles read.
- `python scripts/prepare_serving.py`: success; derives bounds only from frozen Phase 02 train rows and pins manifest/split hashes, no fit/retrain or changes to weights/preprocessor.
- Set PHASE02_TEST_DATABASE_URL/PHASE03_TEST_DATABASE_URL to separate disposable local DBs, then `python scripts/check_phase03.py`: exit 0. Runs full pytest, demo and actual Uvicorn HTTP.
- `python -m pytest backend/tests -v`: **65 passed, 0 skipped, 8 warnings**. Includes all prior contract/MAS/data tests plus real serving, feature order/determinism/no-fit, missing/corrupt/version/feature mismatch, strict API validation, insert/rollback, model-unavailable no-output, PredictionResult in WorkflowState and version in trace.
- PostgreSQL tests execute migrations through 0002_phase03. Phase 02 regression covers upgrade/downgrade; its expected head revision updated for 0002. Integrated insert test checks prediction/run FK and event count. Failure injected after prediction writes proves counts unchanged across assessments/predictions/runs/demo cases/model versions/events.
- `python scripts/demo_prediction.py`: exit 0; three synthetic cases, genuine score and persisted UUID, GET readback assertions. Model pima-mlp-0.2.0, output schema 1.1, runtime 2.1.
- Uvicorn child on temporary loopback port: GET health and /api/v1/models/current, GET run and /trace for previously persisted demo run from a different app process. Verified ID/trace match PostgreSQL snapshot, demonstrating storage independent of process RAM. Child stopped in verifier finally block.

Evidence: [pytest.log](pytest.log), [demo.log](demo.log), [demo.json](demo.json), [uvicorn.log](uvicorn.log), [live_http.json](live_http.json), [results.json](results.json). Exact reproduction commands in root README. No metric changes or training results generated for Phase 03.

## Demo results — SYNTHETIC, not real patients

| SYNTHETIC case | run_id | score | persisted prediction UUID |
|---|---|---:|---|
| SYNTHETIC_CASE_1_NOT_REAL_PATIENT | f73ef4ed-2b42-464e-8454-9716546c106b | 0.015537431463599205 | 404f458f-86ee-4da5-befd-23bf52bc75d1 |
| SYNTHETIC_CASE_2_NOT_REAL_PATIENT | 236cfc17-6a9b-456d-a842-a5da489852ea | 0.21802997589111328 | 458a415c-23a5-40ed-a1c6-a6f1f6f07f64 |
| SYNTHETIC_CASE_3_NOT_REAL_PATIENT | 188becfe-ddb6-47e9-8e25-d5755a003ebc | 0.008898472413420677 | bffb402a-26cf-4925-8b0e-0aea3dc2280a |

Scores are sigmoid model outputs, not calibrated clinical disease probabilities. Numeric classes are threshold outputs only, with no diagnostic labels. Workflow remains DEGRADED because policy/knowledge are unavailable; prediction task is COMPLETED/integrated. Default Education remains abstention, with actual prediction available in agent_results.prediction.output.

## Implementation and contracts

See [ADR 0003](../../decisions/0003-serving-persistence.md). Default main:app and create_app() are integrated, no automatic stub/older-model fallback; prior-phase fixture calls explicitly use prediction_enabled=False. Prediction model is app-owned/lazy-load-once with RLock, torch.eval/inference_mode, frozen preprocessing. Artifact corruption/version/feature/device mismatch yields UNAVAILABLE/no output. GPU optional via MODEL_DEVICE=cuda; CPU actually tested, GPU not tested.

Input uses unchanged AssessmentInput v1.0 plus strict raw JSON numeric check and explicit is_synthetic=true. Out-of-training-range raw values produce warnings, no clipping. Five zero-missing fields are transformed exactly as trained and warn explicitly. Artifact loader never fits preprocessing. Model version/preprocessing checksum/latency/limitations/warnings/persisted ID returned.

PredictionResult v1.0 remains unchanged; serving subclass schema 1.1 adds required metadata. Runtime version explicitly bumped to 2.1 and clients with explicit 2.0 must migrate; no silent compatibility claim. Migration 0002 adds nullable JSON snapshots preserving historical Phase 02 rows. Existing rows without a response are not falsely reconstructed. Controller owns transaction, agent writes pending prediction before returning to Coordinator, commit happens after complete snapshot/events; write failures force rollback/503. No ephemeral success response after failed commit.

New/modified files: [files.txt](files.txt). Trained checkpoint and preprocessing from Phase 02 unchanged; only serving.json added under artifact directory (gitignored and reproducible). Coordinator changes limited to trace metadata/warnings and persistent-mode limitations; order/fallback/Safety unchanged. No separate /predictions endpoint or duplicate inference logic.

## Limitations

Local synthetic-only MVP; confirmation is a caller assertion, not verification that inputs are fabricated. No auth/clinical validation, do not expose publicly or use real patient profiles. Model/data cards and cohort/license limitations still apply. Model score is uncalibrated, no clinical threshold claim. Education still abstains; full Safety/knowledge/RL not implemented.

Synchronous psycopg/inference work is inside async orchestration: limited throughput; asyncio timeout is cooperative, not hard cancellation of blocking work. Default app engine applies connection/statement timeouts. SQL reflection per request adds overhead. Database unavailable returns sanitized 503; no RAM fallback. Registered model digest prevents silently reusing version with different weights. Failed model load is cached until restart; repair requires restart. Artifact hashes detect changes, not malicious authenticity; only trusted local joblib files.

Migration integration tests require explicitly disposable DBs; tests without DB env skip relevant cases and cannot establish acceptance. Verifier rejects skips and requires both URLs. Warnings are existing TestClient/httpx and Alembic config deprecations, no test failure. No frontend changes/build required. No Git repository initialized/commit/push; commit hash none.
