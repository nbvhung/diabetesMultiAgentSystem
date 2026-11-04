# Phase 04 — PASS, READY_FOR_PHASE_05

Report UTC: 2026-11-01T20:49:05.667332+00:00. Only Phase 04 implemented. DL weights/preprocessing/checkpoint and RL unchanged. No full clinical knowledge coverage claimed.

## Actual execution

`python -m pip install "neo4j>=5.24,<7" beautifulsoup4`: success, Neo4j driver 6.4.1, BeautifulSoup already available. Dependency group updated in pyproject.

Downloaded NIDDK overview and copyright page after sandbox network rejection and approved escalation. Loaded real cached HTML, extracted reviewed sentence chunks. No fabricated source text/URL. Source notes: https://www.niddk.nih.gov/health-information/diabetes/overview and https://www.niddk.nih.gov/copyright . Raw HTML cached locally and gitignored; provenance/full normalized excerpts in ingestion.json.

Neo4j Community 5.26.0 portable downloaded, Java 17 used. Unicode repository path failed Java classpath resolution; extracted portable runtime to dedicated ASCII D:/TEMP/diabetes-neo4j-phase04. Bound only 127.0.0.1:17687/17474, no auth for isolated temporary graph. Initial seed before server readiness returned UNAVAILABLE; after Started, seeding succeeded. No fabricated graph metrics or mock server used.

Set NEO4J_TEST_URI to dedicated graph, PHASE02_TEST_DATABASE_URL and PHASE03_TEST_DATABASE_URL to separate disposable PostgreSQL DBs, then `python scripts/check_phase04.py`: exit 0. Script ran:

- `python scripts/seed_knowledge.py`: PASS, **30 nodes / 48 relationships / 19 chunks**. Two sequential imports identical counts: idempotence demonstrated. Nine constraints/index tested.
- `python scripts/evaluate_knowledge.py`: PASS; 24 labeled author questions, all three strategies actually executed against Neo4j. Detailed per-query labels/IDs/timing in experiments/results/phase04/retrieval_evaluation.json; summary CSV exported.
- `python -m pytest backend/tests -v`: **77 passed, 0 skipped, 8 deprecation warnings**. Includes source URL/metadata, lexical embedding vector search, actual graph traversal, hybrid, constraints/idempotence/connectivity, no evidence, simulated unavailable and synthetic prompt-injection, Coordinator invoking real KnowledgeAgent, and all existing prediction/PostgreSQL/MAS/data regressions.
- Actual ASGI API workflow: POST question → Coordinator → integrated Knowledge → Neo4j hybrid → grounded Education → Safety → PostgreSQL snapshot; response evidence IDs present in final text. GET run equals stored response; knowledge health 200. Proof: api_workflow.json. This check uses TestClient, not a separate live HTTP network server; no claim of a Phase 04 browser/live-network test.

Logs: seed.log, evaluation.log, pytest.log, results.json. PostgreSQL temporary cluster stopped after test. Neo4j console does not register as a Windows service (`neo4j stop` reported not running); stopped only Java PIDs verified by command lines containing this phase's isolated temporary home. Existing Neo4j/PostgreSQL services were not altered.

## Retrieval results — actually measured

| Strategy | Recall@5 | MRR@5 | Citation provenance | No-evidence accuracy | Mean ms |
|---|---:|---:|---:|---:|---:|
| vector | 0.540833 | 0.751667 | 1.000 | 1.000 | 30.053 |
| graph | 0.920000 | 0.925000 | 1.000 | 1.000 | 14.345 |
| hybrid | 0.917500 | 0.925000 | 1.000 | 1.000 | 43.999 |

20 answerable queries, 4 ambiguous/out-of-scope negatives; gold relevance is source-section-level sentence IDs. Citation metric means exact ID/text/URL correspondence with accessed corpus, not physician-reviewed clinical entailment. Latency includes read/traversal/ranking, local warm-cache measurements, not production P95. Hybrid is slightly below graph Recall@5 here; no claim hybrid always improves retrieval. No-evidence negatives are deliberately small/easy, not robust open-domain safety validation.

## Files and design

- backend/app/knowledge/store.py: allowlisted loader, normalization, reviewed chunking/mapping, metadata, hashing embedding and idempotent Neo4j import/read queries.
- backend/app/rag/retrieval.py: common Retriever Protocol and vector/graph/hybrid strategies, parameterized graph reads, dedup/RRF.
- backend/app/mas/agents/knowledge.py: real KnowledgeAgent and deterministic citation-grounded EducationAgent.
- backend/app/api/knowledge.py: debug health/search/summary endpoints.
- scripts/seed_knowledge.py, scripts/evaluate_knowledge.py, scripts/check_phase04.py.
- experiments/configs/knowledge_eval.json; experiments/results/phase04/retrieval_evaluation.json and retrieval_summary.csv.
- backend/tests/test_knowledge_phase04.py: 12 new tests/cases.
- Modified main.py, api/mas.py, api/system.py, core/config.py for wiring/config; Coordinator only adds NO_EVIDENCE reason/warning and accurate limitations, not agent order or clinical logic.
- Updated AGENTS.md, README, pyproject.toml, .gitignore, docs/architecture.md, docs/agent_contracts.md, docs/phase_status.md. Added docs/knowledge_graph.md and docs/rag_pipeline.md. Existing runtime schema 2.1/EvidenceItem v1 unchanged; empty search is COMPLETED+evidence=[] with NO_EVIDENCE trace/warning, infrastructure failure UNAVAILABLE.

## Limitations

Initial corpus is only NIDDK overview cards: names diabetes types and gives brief risk/symptom/tests/lifestyle/prevention/care-team information. No detailed type-specific mechanisms, diagnostic thresholds or formal ADA/WHO guidelines ingested. Guideline node is explicitly educational overview, not clinical Standards of Care. Stronger relation names are documented reserved vocabulary; implemented graph uses RELATED_TO/SUPPORTED_BY/HAS_CHUNK/REFERENCES, no inferred medical causation. No Pima statistics enter graph.

Vector retrieval is stateless 512-dimensional hashing lexical embedding + exact cosine over bounded <=1000 Neo4j chunk vectors, not pretrained semantic embedding or native ANN index. Limited bilingual aliases and corpus size; off-topic queries containing known medical keywords may still return general excerpts. Historical chunks retained on future content updates; review source versions before reuse. Ingestion upsert is idempotent for identical input, not a source-retirement system.

No LLM; Education quotes admitted exact source excerpts and abstains without evidence. Pattern filtering is not a complete prompt-injection detector; deterministic templates cannot execute retrieved instructions/tools. Minimal Safety still applies. Full clinical content validation/auth/RBAC, async scalable retrieval and production deployment are not claimed. Temporary Neo4j auth disabled only on loopback; deploy authenticated/read-only credentials where available. Driver read routing is not an authorization boundary. Keys never derived from user Cypher.

No new diagnostic claims or dose instructions generated. NIDDK majority-copyright-free policy is not blanket permission for third-party images/logos or ADA/WHO text. No commit/push, repository not initialized. No Phase 05 implementation.
