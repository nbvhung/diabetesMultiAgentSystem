# Grounded diabetes expansion — actual verification report

This is the full offline regression snapshot from 2026-11-02T17:32Z. Since then, the user configured credentials, a separate authenticated local Neo4j instance was prepared, and a real six-agent API workflow with Groq generation/review was verified. See [the newer local environment report](../local_environment/report.md). The remaining NOT_RUN in the old snapshot refers to that execution; the new smoke test is not a substitute for the full LLM-quality benchmark or clinical review.

**IMPLEMENTED_PENDING_LIVE_LLM_VALIDATION.** Local software checks pass; the new live-LLM readiness gate is **BLOCKED** until actual Groq generation/review and source review are executed. This user-authorized work extends Phase 07 before Phase 08; Phase 08 remains unimplemented. Historical Phase 07 READY_FOR_PHASE_08 refers to its narrower no-LLM acceptance scope, not this expanded conversational requirement.

Verified UTC: 2026-11-02T17:32:03.071418+00:00. Code: `source-sha256:927ed5c179c660560625a8c1362ae8ceef22706e6669f4a187a5afe8f63d5166`. This workspace has no initialized Git repository; manifests use the complete source-file SHA256 map, not an invented commit. [Machine results](results.json), [protocol](../../diabetes_expansion_experiments.md), [current setup/demo](../../diabetes_expansion_demo.md), [ADR 0007](../../decisions/0007-diabetes-grounded-llm-runtime.md).

## Delivered behavior

- Frozen research MLP and educational Q-policy integrate with real SQL persistence in runtime 3.0. All twelve DL/RL files match the historical Phase 07 digests and the final before/after map. No new LLM training, DL training or clinical RL.
- Fourteen fetched/versioned NIDDK diabetes education pages, 449 admitted paragraph/list chunks, parent section context and eleven exact-clause-supported KG assertions. Current corpus SHA256: `9bc475f0262cb2e45f985a8c1bb671b29828fb944eb6fdf1cee033e38fea5724`. [Graph ingestion/proofs](graph_ingestion.json), [data catalog](../../diabetes_data_catalog.md).
- CPU multilingual sentence encoding and cross-encoder ranking use pinned upstream pretrained models and checksum-validated local assets. Neo4j is genuinely queried; missing graph never masquerades as successful local retrieval.
- Six typed agents: Prediction, Knowledge, RL, Education, Evidence Verifier and Safety. Coordinator sends correlated tasks, performs at most two retrievals/two drafts/four provider attempts, uses reason-only feedback and requires final publication admission plus input/output Safety veto.
- Groq adapter accepts structured atomic claims with exact support IDs/quotes. A separate semantic-review call cannot waive local provenance/number/render checks; Coordinator repeats those checks. Missing/rejected provider responses use labeled original-source excerpts or controlled clarification. Mocked transports appear only in explicit software tests, never in measured model results.
- React uses the real v2 API, six-agent monitor, exact source links, generation/proof labels, source catalog and measured figures. Original v1/runtime 2.4 and old snapshot versions remain supported. No SQL DDL migration or relabeling of old data.

## Executed verification

Final `python scripts/check_diabetes_expansion.py`: exit 0. Requires dedicated PHASE02_TEST_DATABASE_URL, PHASE03_TEST_DATABASE_URL, NEO4J_TEST_URI and a compatible installed Chromium. Migration tests use a different disposable database from run persistence.

| Command / layer | Actual result | Evidence |
|---|---|---|
| `python -m pytest backend/tests -q` | 243 passed, no failures/skips; eight deprecation warnings | [pytest.log](pytest.log) |
| Frontend `npm test` (same Vitest CLI) | 18 passed | [frontend_unit.log](frontend_unit.log) |
| Frontend `npm run build` | TypeScript/Vite exit 0 | [frontend_build.log](frontend_build.log) |
| `evaluate_diabetes_rag.py`, `evaluate_diabetes_mas.py`, `evaluate_diabetes_safety.py` | Actual measured CSV/JSON/PNG; exit 0 | individual logs in this directory |
| `run_diabetes_demo.py --base-url http://127.0.0.1:8000` | 5/5 actual workflows, committed GET/trace equality | [demo_runs.json](demo_runs.json), [demo.log](demo.log) |
| Frontend `npm run test:e2e` (same Playwright CLI) | 6 passed; no skipped/flaky/retries | [browser.log](browser.log), [browser-results.json](browser-results.json) |
| Frozen artifacts / experiment integrity | All original model/policy digests equal; new report output hashes and source versions verified | [results.json](results.json) |

New tests cover actual graph/model/SQL integration, VI/EN retrieval, all six statuses, weak-evidence feedback and recovery, synthetic assessment validation, four concurrent durable runs, old v1 compatibility, missing model/graph/policy/key, bounded repair, timeout, missing Safety, provider auth/rate/truncation/model errors, quote/number forgery, compromised verifier approval, rejected-draft erasure, proof/snapshot tampering, exact KG clauses and idempotent graph ingestion. Provider transport tests are explicitly synthetic, not live Groq results.

This run used dedicated PostgreSQL on loopback port 55432 and Neo4j Community 5.26.0 on Bolt 17687/HTTP 17474 with Java 17. The runner stopped its own API/Vite children; the dedicated database/graph services started for validation were also stopped after completion. Start actual PostgreSQL/Neo4j and configure their URLs before launching the demo or running live LLM evaluation. No unrelated service was stopped.

## First-pass retrieval measurement

Same 125 project-authored synthetic questions across lexical, semantic, graph and hybrid; 40 development + 40 diagnostic + 40 additional confirmatory phrasings + 5 unanswerable. No patient data. Coarse manual source/section targets are not expert clinical ground truth. The additional phrasing questions were fixed after first-pass architecture/threshold selection; topics and source documents overlap. A later retry fix used a separate development safety case, without changing first-pass thresholds. These results are descriptive, not external or clinical validation.

The following table is the 40-question confirmatory first-pass split. Maximum three returned chunks, never padded to k; hybrid performs additional cross-encoder work. Recall denominator is all target source-section chunks, which can exceed three. Exact citation provenance only proves the passage/source identity, not clinical correctness.

| strategy | queries | recall_at_3 | precision_at_returned | mrr_at_3 | citation_provenance | latency_ms |
| --- | --- | --- | --- | --- | --- | --- |
| lexical | 40 | 0.151806 | 0.208333 | 0.295833 | 1.000000 | 30.356368 |
| semantic | 40 | 0.313819 | 0.362500 | 0.575000 | 1.000000 | 69.531045 |
| graph | 40 | 0.293472 | 0.391667 | 0.508333 | 1.000000 | 30.587655 |
| hybrid | 40 | 0.290972 | 0.570833 | 0.625000 | 1.000000 | 1009.579682 |

Hybrid has higher mean returned-passage precision/MRR here; semantic-only has higher Recall@3 and lower latency. Do not claim hybrid wins every metric. All four strategies correctly return no evidence for the five fixed unanswerable questions; this small set does not establish general out-of-domain robustness. [CSV](../../../experiments/results/diabetes_rag.csv), [row-level JSON](../../../experiments/results/diabetes_rag.json), [figure](../../../experiments/figures/diabetes_rag.png), [manifest](../../../experiments/results/diabetes_rag.manifest.json).

## Multi-agent comparison

Same model/tool/evidence access, actual Neo4j and source checks. Twenty-two cases repeated twice per method (44 runs, not 44 independent questions): twelve diagnostic question forms from the first six topic families, five unanswerable questions and five adversarial requests. This comparison does not cover every corpus topic. Provider is explicitly disabled in both; these are genuine extractive/clarification/refusal workflows and contain **zero generated LLM answers**. No generated-answer quality or clinical effect is inferred.

| method | runs | task_completion | evidence_relevance | citation_provenance | safety_invariants | latency_ms | llm_generated_runs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| single_workflow | 44 | 0.727273 | 0.750000 | 1 | 1 | 435.450548 | 0 |
| multi_agent | 44 | 0.863636 | 0.650000 | 1 | 1 | 593.688205 | 0 |

The direct workflow uses one fixed retrieval/draft; MAS can retrieve twice and repair within its declared budget. Thus the comparison includes additional control/tool computation and does not isolate agent decomposition under equal call budgets. Higher observed task completion comes with additional latency; evidence relevance is a conditional mean over runs with released evidence and different denominators. Identical provenance/safety invariants do not establish clinical safety. This small descriptive benchmark is not proof that MAS is generally superior. Some otherwise safe questions still fail task completion, including conservative content blocking; failures remain in row-level outputs.

RL still proposes a simulator-trained educational action. Verified response mode can override it and records both actions/reason honestly; learner benefit from those actions is not established. The existing unchanged DL held-out and RL simulator comparisons remain in [Phase 07 report](../phase07/report.md); no new training metric was fabricated.

[MAS CSV](../../../experiments/results/diabetes_mas.csv), [rows/JSON](../../../experiments/results/diabetes_mas.json), [figure](../../../experiments/figures/diabetes_mas.png), [manifest](../../../experiments/results/diabetes_mas.manifest.json).

## Safety and failure measurements

| layer | cases | passed | pass_rate |
| --- | --- | --- | --- |
| actual_coordinator_fault | 2 | 2 | 1 |
| actual_workflow | 8 | 8 | 1 |
| rules | 4 | 4 | 1 |

These fourteen cases comprise eight actual workflow scenarios, two explicit synthetic agent faults and four rule probes. This finite regression pass does not override other safe-question task failures or certify adversarial/clinical performance. A forged-quote fault tests provenance rejection, not reasoning over two authentic conflicting clinical guidelines. Missing dependencies and other provider/contract faults are covered in the backend suite separately.

[Safety CSV](../../../experiments/results/diabetes_safety.csv), [detail JSON](../../../experiments/results/diabetes_safety.json), [figure](../../../experiments/figures/diabetes_safety.png), [manifest](../../../experiments/results/diabetes_safety.manifest.json).

## Actual demos and screenshots

| scenario | status | generation_mode | passed | transport |
| --- | --- | --- | --- | --- |
| synthetic_assessment_and_risk | DEGRADED | extractive | 1 | TCP HTTP |
| vietnamese_education | DEGRADED | extractive | 1 | TCP HTTP |
| unsafe_medication | BLOCKED | withheld | 1 | TCP HTTP |
| missing_evidence | DEGRADED | clarification | 1 | TCP HTTP |
| neo4j_outage | DEGRADED | clarification | 1 | ASGI explicit graph fault injection |

Normal assessment/risk and Vietnamese symptoms use genuine frozen inference/retrieval/persistence. Medication-dose request is vetoed before business-agent dispatch. Missing evidence triggers bounded retrieval and controlled clarification; isolated Neo4j fault returns unavailable with no citations. These demo runs intentionally disable the remote provider, so source excerpts are not represented as LLM answers.

[Overview](overview.png), [assessment/evidence](assessment.png), [six-agent trace](monitor.png), [unsafe request](unsafe.png), [graph unavailable](knowledge-unavailable.png), [clarification](clarification.png), [experiments](experiments.png), [mobile](mobile.png). Screenshots are actual Playwright captures; desktop overview was visually inspected.

## Live LLM gate and remaining work

Groq status: **NOT_RUN / GROQ_API_KEY_NOT_CONFIGURED**, zero remote requests and `quality_metrics=null`. [Actual status](llm_live_status.json). No LLM quality CSV/figure was invented. Configure `GROQ_API_KEY` yourself in the ignored project `.env`, never in chat/frontend; restart backend and run:

```powershell
python scripts/evaluate_diabetes_llm.py --live --limit 6
```

See [provider/grounding setup](../../llm_grounding.md). Even after genuine provider calls, approved responses still need human source review; an LLM reviewing another call is fallible and its acceptance rate is not medical accuracy. No claim is made that this system has been trained to ChatGPT capability or is a clinically validated diabetes advisor.

Other limits: one publisher/English public sources, coarse small bilingual benchmark, conservative false positives, manually curated miniature KG, incomplete personal-identifier redaction, single-turn requests and post-run trace, simulator-only RL, no production authentication/rate limiting or deployment. Blocking CPU/driver work is not fully preemptible by asyncio. Use synthetic research inputs only.

Initial safe-activity regression failure was retained in [before_retry_fix/](before_retry_fix/); the expected education label was unchanged. Retry ranking was corrected and a genuine API recovery test added. KG source-clause audit and fixes are documented in the protocol. Final measurements were regenerated after the final code changes, and all three new experiment manifests match the final source version.

No Git init/commit/push, no old assignment edits, and no Phase 08 implementation.
