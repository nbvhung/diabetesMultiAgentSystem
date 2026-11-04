# Phase 07 — verified implementation and experimental report

**READY_FOR_PHASE_08** within the local research/course acceptance scope. Phase 08 not implemented. Verified UTC: 2026-11-02T14:03:11.366411+00:00.

Code version: `source-sha256:6e300213edbb82d84ef47370ee421acd999ad9cda1b31fab94abeafb7eca7b45`. Workspace is not a Git repository, so manifests use a full source SHA256 map and git_commit=null. Frozen Phase 02 model/preprocessing and Phase 06 policy artifacts are unchanged; before/after digests in [results.json](results.json).

## Delivered scope and acceptance evidence

| Acceptance item | Executed evidence |
|---|---|
| React / TypeScript / Vite five-screen UI | Overview, Assessment, Knowledge assistant, Execution monitor, Experiments; production build exit 0 and browser screenshots |
| Real API and full MAS chain | Browser/API assessment + question → Coordinator + Prediction + Knowledge + RL + Education + two Safety gates; no canned frontend outputs |
| Real dependencies and persistence | Frozen PyTorch checkpoint; existing Neo4j corpus; serving Q policy; migrated PostgreSQL synthetic assessment/prediction/run/events; GET snapshot/trace equality |
| Correlated trace and explainability | Run/message IDs, sequence order, agent statuses, Coordinator reasons, RL proposed/effective action/source/version, Safety rule IDs, redacted summaries |
| At least three executed demo scenarios | Four executed cases below; first three over TCP HTTP and separate Neo4j outage via actual ASGI app; browser also executes normal/veto/outage |
| Actual evaluations and figures | E1–E5 summary/rows CSV, detail JSON, five PNGs and six complete provenance manifests; artifact hashes verified through API |
| Important error tests | Model missing, Neo4j missing, invalid assessment, Safety veto, missing policy fallback, timeout, altered/conflicting provenance, injection, citation links and four concurrent isolated persisted runs |
| No fabricated metrics/citations | Missing/unmanifested/tampered reports withheld; actual source ID/excerpt/URL admission; browser loads verified PNGs; empty evidence displays no source links |

## Actual verification commands

Final `python scripts/check_phase07.py`: exit 0. Environment names: PHASE02_TEST_DATABASE_URL, PHASE03_TEST_DATABASE_URL, NEO4J_TEST_URI, optional PHASE07_CHROMIUM_PATH. Two separate disposable PostgreSQL databases were used; migration regression never targets the persistence/demo DB. This runner owns and stops only its child API/Vite processes. It does not stop unrelated infrastructure.

- `python -m pytest backend/tests -q`: **191 PASS, 0 FAIL, 0 skipped**, eight known deprecation warnings. [pytest.log](pytest.log).
- `npm test` (runner invokes the same Vitest CLI directly): **18 PASS**. [frontend_unit.log](frontend_unit.log).
- `npm run build`: TypeScript + Vite exit 0. [frontend_build.log](frontend_build.log).
- `python scripts/evaluate_prediction.py`, `evaluate_rag.py`, `evaluate_mas.py`, `evaluate_rl.py`, `evaluate_safety.py`: all exit 0. Corresponding logs are in this directory.
- `python scripts/run_e2e_demo.py --base-url http://127.0.0.1:8000`: **4/4 executed and persisted/read back**, exit 0. [e2e.log](e2e.log).
- `npm run test:e2e` (runner invokes the same Playwright CLI directly, with owned external test servers): **5 PASS, 0 skipped, 0 flaky/retries**, exit 0. [browser.log](browser.log), [machine-readable browser results](browser-results.json).

Initial npm sandbox network denial required approved dependency installation. An early evaluator read failed on the Windows default text encoding and was corrected to explicit UTF-8. A first browser run completed its assertions but Windows webServer cleanup stalled; verified owned processes were stopped, and the final reproducibility runner uses direct child process handles. The final commands/logs above all completed normally. No failed assertion or benchmark label was removed to create a pass.

## E1 — same held-out test split

| model | accuracy | precision | recall | f1 | roc_auc | pr_auc |
|---|---|---|---|---|---|---|
| MLP | 0.758621 | 0.709677 | 0.536585 | 0.611111 | 0.863415 | 0.781957 |
| LogisticRegression | 0.775862 | 0.777778 | 0.512195 | 0.617647 | 0.862439 | 0.783225 |
| RandomForest | 0.732759 | 0.666667 | 0.487805 | 0.563380 | 0.827967 | 0.757576 |

Same 116 held-out test indices and frozen train-only preprocessing; threshold 0.5. MLP was not retrained. PR-AUC means average precision. Logistic Regression has slightly higher accuracy/F1 here; no MLP superiority claim. [CSV](../../../experiments/results/prediction.csv), [JSON](../../../experiments/results/prediction.json), [figure](../../../experiments/figures/prediction.png).

## E2 — same 24 queries and corpus

| strategy | recall_at_5 | mrr_at_5 | citation_correctness | citation_count | no_evidence_accuracy | latency_ms |
|---|---|---|---|---|---|---|
| vector | 0.540833 | 0.751667 | 1.000000 | 82 | 1 | 20.862079 |
| graph | 0.920000 | 0.925000 | 1.000000 | 61 | 1 | 8.468413 |
| hybrid | 0.917500 | 0.925000 | 1.000000 | 89 | 1 | 29.073846 |

Citation correctness checks exact source provenance. Vector retrieval is lexical hashing, not a learned dense model. Latencies are descriptive local single-pass observations subject to cache/warmup; no speed superiority inference. [CSV](../../../experiments/results/rag.csv), [JSON](../../../experiments/results/rag.json), [figure](../../../experiments/figures/rag.png).

## E3 — same-tool single workflow vs MAS

| method | tasks | task_completion | evidence_correctness | citation_provenance | evidence_cases | safety_pass_rate | latency_ms | latency_p95_ms |
|---|---|---|---|---|---|---|---|---|
| single_workflow | 36 | 0.916667 | 0.520000 | 1 | 15 | 1 | 87.622028 | 290.520825 |
| multi_agent | 36 | 0.916667 | 0.520000 | 1 | 15 | 1 | 66.250147 | 158.012525 |

12 project-authored SYNTHETIC scenarios × 3 repeats per method, paired shuffled order. Baseline directly calls the same model/retrieval/policy/templates/rules and shares only the refusal-formatting helper with Coordinator; it never runs Coordinator orchestration, registry dispatch or agent execution. Prediction DB writes and rollback timing scope are the same. MAS is the actual five-agent orchestration.

Evidence correctness is section relevance AND admitted provenance, not just URL validity; empty evidence is excluded (evidence_cases reported). Provenance alone is reported separately. Both methods have the same completion/evidence/safety outcomes. The benchmark therefore **does not establish MAS superiority**. Coordination, state isolation, veto control and auditability are demonstrated independently of prediction accuracy. Latency differences are observed on this host without significance testing.

Paired output mismatches (status/score/IDs/action/response hash): **0**. Known failed completion scenario: S04, all three repeats in both methods. Safety blocks an otherwise safe lifestyle question because a retrieved conditional source sentence contains the phrase “you have diabetes”. Expected label remains educational success; this stays a failure rather than being relabeled to BLOCKED. No unsafe medication content was released in the tested scenarios.

[CSV](../../../experiments/results/mas.csv), [per-execution rows](../../../experiments/results/mas_rows.csv), [JSON](../../../experiments/results/mas.json), [figure](../../../experiments/figures/mas.png).

## E4 — paired simulator seeds

| policy | average_episode_reward | completion_rate | reward_variance_across_scenarios | unsafe_action_attempts | mean_episode_length | fallback_decisions |
|---|---|---|---|---|---|---|
| q_learning | 4.276000 | 0.970000 | 8.358457 | 0 | 2.470000 | 5 |
| rule_based | 4.311000 | 0.983333 | 8.504162 | 0 | 2.036667 | 0 |

300 held-out seeds, exported serving selector/fallback parity checked. Rule baseline outperforms Q on mean reward and completion. Simulator reward is not a health or measured education outcome. Actual Phase 06 training history is the curve input, with its checksum in the manifest; Phase 07 did not retune or retrain the policy. [CSV](../../../experiments/results/rl.csv), [JSON](../../../experiments/results/rl.json), [reward curve](../../../experiments/figures/rl.png).

## E5 — rule fixtures and workflow faults

| layer | cases | passed | pass_rate |
|---|---|---|---|
| rules | 41 | 41 | 1 |
| workflow | 14 | 13 | 0.928571 |

41/41 deterministic rule fixtures; 13/14 workflow expected behaviors. The missed workflow expectation is the same safe-query S04 false positive, not an unsafe release. Evaluator exits successfully after recording imperfect performance; its invariant checks still fail execution on unsafe-release/rule failures. Regression execution PASS is distinct from benchmark performance.

Conflicting evidence probe alters a real-source quote, demonstrating provenance rejection and output withholding. It does not claim resolution of two medically conflicting but valid sources. Timeout is an intentionally slow async agent, not proof of interruption of every synchronous driver call. [CSV](../../../experiments/results/safety.csv), [JSON](../../../experiments/results/safety.json), [figure](../../../experiments/figures/safety.png).

## Executed demo records

| scenario | run_id | status | passed | transport |
|---|---|---|---|---|
| normal_education | a649659f-0e67-49d6-b55f-fc2ea49afd44 | DEGRADED | 1 | live HTTP |
| coordination | 6fd7620b-79f8-463c-b0ee-2c757eb747aa | COMPLETED | 1 | live HTTP |
| unsafe_medication | 19b6b63a-ee89-4d20-b795-27aad19f3cda | BLOCKED | 1 | live HTTP |
| knowledge_unavailable | 2d3fce6b-aeb4-41b9-97f3-88052fece4ce | DEGRADED | 1 | ASGI HTTP |

All response bodies are generated by actual workflows and read back from SQL, with ordered input/output Safety decisions and correlated trace. Knowledge failure is isolated dependency injection; production API has no public fault switch. [Full runs/trace](../../../experiments/results/e2e.json), [manifest](../../../experiments/results/e2e.manifest.json).

## Screenshots

[Overview](overview.png) · [Assessment](assessment.png) · [Execution monitor](monitor.png) · [Safety veto](unsafe.png) · [Knowledge unavailable](knowledge-unavailable.png) · [Experiments](experiments.png) · [Mobile](mobile.png).

## Remaining limits and readiness decision

All Phase 07 delivery acceptance items above are evidenced: real frontend/API, all five agent integrations, durable trace, four actual demos, actual experiment bundles and important fault regression checks. **READY_FOR_PHASE_08** denotes this local software/research delivery, not 100% benchmark completion or clinical readiness. The S04 false positive and simulator/bounded-corpus limitations remain explicitly visible in source scenarios, measured results and this report. No Phase 08 implementation.

Corpus remains the narrow NIDDK overview; no broad clinical coverage/entailment or general conflict-reasoning claim. UI trace is post-run, not streaming. Concurrency tests establish isolation/persistence, not distributed throughput. No clinical validation, auth or production deployment was added. Existing deprecation warnings remain. Neo4j test startup used the host's default Java 23.0.1 and logged an unsupported-runtime warning (actual software checks passed); use the supported Java runtime documented for Neo4j when reproducing a deployment. PostgreSQL 17.7, Node v24.14.1 and dependency versions are recorded in logs/manifests.

Protocol/commands: [demo guide](../../demo_guide.md), [experiments](../../experiments.md). SHA256 output admission proves local integrity, not an attacker-resistant signature. No Git init/commit/push or assignment changes were made.

After verification, the runner stopped its owned API/Vite children. The dedicated temporary PostgreSQL cluster started for this session was stopped with pg_ctl, and only Neo4j Java processes whose command lines matched the verified temporary test home were stopped. Local services are not left running; start dependencies and use demo_guide.md to launch the interactive demo. Persisted synthetic runs and all evaluation/screenshot artifacts remain available on disk.
