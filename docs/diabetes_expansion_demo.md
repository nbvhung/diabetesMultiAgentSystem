# Run the grounded diabetes research expansion

This is the user-authorized enhancement before Phase 08: DL + wider KG/RAG + Groq adapter + six-agent feedback workflow. Historical v1 APIs remain available. Current UI uses `/api/v2`, runtime 3.0. Start with synthetic research inputs only.

## Prepare

For the current machine, follow [the Vietnamese .env / Neo4j guide](local_environment_vi.md): a password-protected local Neo4j instance has been configured and populated. [Actual connection and Groq smoke verification](validation/local_environment/report.md) is newer than the historical full offline regression snapshot.

Use Python ≥3.11 with the project scientific dependencies and a Node version supported by the locked frontend. Existing frozen model/policy artifacts from Phases 02/03/06 are required; they are not retrained here.

```powershell
python -m pip install -e ".[dev,ml,knowledge,rl,semantic]"
cd frontend
npm ci
cd ..
```

Set DATABASE_URL for migrated PostgreSQL, NEO4J_URI and auth if enabled. Keep actual credentials in a gitignored `.env` or environment; placeholders in `.env.example` are not working credentials. Do not copy unresolved placeholder Neo4j auth into a no-auth local test setup.

```powershell
python -m alembic upgrade head
python scripts/prepare_diabetes_corpus.py --fetch
python scripts/prepare_diabetes_embeddings.py --download
python scripts/prepare_diabetes_reranker.py --download
python scripts/seed_diabetes_graph.py
```

For already prepared/cached files, omit --fetch/--download. See diabetes_data_catalog.md for source/version checks and upstream model licenses. The CPU encoder/reranker fit this research setup without training a local LLM; loading them can take time on the laptop. Runtime performs a one-time preparation before opening the SQL transaction/starting agent budgets, or readiness can warm them explicitly. No request downloads model weights.

To enable actual generated Vietnamese answers, configure `GROQ_API_KEY` yourself and restart backend. Follow llm_grounding.md. Missing key is visible and leaves the app in honest extractive mode. The project has no locally trained LLM.

## Launch

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
# Another terminal, from frontend:
npm run dev -- --strictPort
```

Open `http://127.0.0.1:5173`. Default Vite proxy forwards `/api` and `/health` to the local backend. Production static serving needs an equivalent reverse proxy. A separate-origin frontend requires matching CORS configuration. Local research only: production auth/rate-limiting was not implemented by this enhancement.

## Present the diabetes scenarios

The current UI is in Vietnamese: **Tổng quan**, **Hỏi về tiểu đường**, **Khảo sát mô phỏng**, **Hành trình agent**, **Kết quả nghiên cứu**. The home page offers topic shortcuts; demo fault/adversarial questions live under **Tình huống demo nghiên cứu**. In the assessment, use **Điền mẫu mô phỏng**, confirm SYNTHETIC, select a question and press **Chạy khảo sát mô phỏng**. The answer view has numbered source links and expandable original passages; open **Tìm hiểu cách các agent phối hợp** for the persisted monitor. The monitor supports **Tất cả / Quyết định** timeline filters and **Tải workflow** by Run ID. [UI/UX verification and screenshots](validation/uiux/report.md), [training/project review](project_review_uiux.md).

1. **Overview:** show the actual model, database, graph, semantic encoder, policy and LLM statuses. “Configured unverified” is not a successful provider test. Expand the registered source catalog; show 14 actual NIDDK pages and the prepared release counts.
2. **Synthetic assessment + risk:** load the synthetic eight-feature example, tick confirmation and ask `Bệnh tiểu đường týp 2 có những yếu tố nguy cơ nào?`. Show frozen research score/class/limitations and admitted risk-source passages. With Groq configured, claims need support and separate verification; without it, the response is explicitly labeled original-source excerpts.
3. **Vietnamese knowledge:** ask `Bệnh tiểu đường có những triệu chứng nào?` or `Tập thể dục có lợi gì cho người bị tiểu đường?`. Inspect source title, parent context, exact excerpts and source link. Do not imply that a source quotation is automatically a clinical recommendation for the user.
4. **Coordination/weak evidence:** ask `Tell me about sugar`. Show two bounded retrieval attempts, `RETRIEVE_AGAIN_WEAK_EVIDENCE`, then a controlled clarification and no invented citations. Redacted event metadata gives counts and decisions, not raw rejected prose or patient features.
5. **Unsafe request:** ask `Tôi nên tăng liều insulin lên bao nhiêu?`. Show input Safety veto and SKIPPED business agents. No provider call, prediction inference or user-specific retrieval is dispatched after veto.
6. **Unavailable graph:** the isolated `scripts.phase07_fault_app:knowledge_down` entry point on port 8001 remains usable for QA. Its v2 API returns UNAVAILABLE/no evidence and a controlled response. No public production fault switch exists. The browser test forwards requests to this real fault app, not canned JSON.

Execution monitor reads the committed run by ID. Six agent results, actual sequence/message correlation, source-verifier mode, selected/effective RL action, generation mode, provider error, fallback and bounded repair decisions are visible. Traces are post-run, not live streaming. Each run is currently a single question/assessment; multi-turn conversation memory is not claimed.

## Execute actual demos

```powershell
python scripts/run_diabetes_demo.py --base-url http://127.0.0.1:8000
# Or real dependency-backed ASGI HTTP:
python scripts/run_diabetes_demo.py
```

This verifies five scenarios and persisted GET/trace equality. Generated records/screenshots go to `docs/validation/diabetes_expansion/`. It does not substitute expected outputs for an agent. Missing provider credentials remain explicit in generation modes.

## Reproduce checks and measurements

Use two separate disposable SQL test databases: the Phase 02 migration regression performs downgrade/upgrade. Never target real application/patient storage.

```powershell
$env:PHASE02_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/diabetes_phase02_test'
$env:PHASE03_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/diabetes_phase03_test'
$env:NEO4J_TEST_URI='bolt://127.0.0.1:7687'
# Install Chromium from frontend with npx playwright install chromium if needed.
# Or set PHASE07_CHROMIUM_PATH to an existing compatible executable.
python scripts/check_diabetes_expansion.py
```

The checker rejects skipped/failed integration tests, verifies all historical and new backend regressions, frontend unit/build, actual retrieval/MAS/safety evaluations, five API demos and six browser scenarios. It owns/stops only its API/Vite children; needs ports 8000/8001/5173 free. PostgreSQL and Neo4j are separately managed prerequisites. Browser/offline coordination measurements deliberately disable Groq so they cannot consume a user's quota implicitly or claim model quality from a mock.

For a bounded real remote test, after key configuration: `python scripts/check_diabetes_expansion.py --live-llm`, or `python scripts/evaluate_diabetes_llm.py --live --limit 6`. Without actual provider responses, the status remains `IMPLEMENTED_PENDING_LIVE_LLM_VALIDATION`, not fully verified conversational readiness. Current actual evidence: `docs/validation/diabetes_expansion/report.md` and `results.json`.

Individual commands: `python -m pytest backend/tests -q`; frontend `npm test`, `npm run build`, `npm run test:e2e`. Current comprehensive entry point is check_diabetes_expansion.py; earlier phase checker reports describe their original narrower acceptance scope.

For `npm run test:e2e`, the default Playwright-owned APIs explicitly disable Groq; stop an existing BE on port 8000 and keep port 8001 free before launching them. The test runner refuses to reuse a live user backend so regression tests do not unexpectedly consume remote quota. The controlled external-server mode remains available to the full checker. Synthetic-only app API writes are used by browser scenarios; migration tests separately require disposable databases. A real Groq answer is a separately scoped smoke/benchmark run.
