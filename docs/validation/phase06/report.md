# Phase 06 — PASS, READY_FOR_PHASE_07

UTC report: 2026-11-02T08:42:24.493714+00:00. Scope only Phase 06: offline synthetic educational Q-learning and integration. No clinical action/dosing/diagnosis objective, no DL checkpoint/preprocessor retraining, no Phase 07 implementation.

## Actual commands and outcomes

- `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/04_rl_q_learning_training.ipynb --ExecutePreprocessor.timeout=600`: executed from beginning to end, exit 0; real Q initialization, epsilon-greedy, Bellman updates, 24,000 total training episodes (3×8000), early environment validation, plots, baseline/held-out evaluation and export. [notebook.log](notebook.log). Final acceptance command re-executed the full notebook, not merely inspected a checkpoint.
- `python scripts/evaluate_rl.py`: exit 0, reloads the exported numeric policy and evaluates it on 300 paired held-out seeds against fixed rule baseline; no training in evaluation. [evaluation.log](evaluation.log).
- `python -m pytest backend/tests/test_rl_phase06.py -q`: initial 21 RL tests passed; later selection-metadata regression added and included in full suite.
- `python scripts/check_phase06.py --execute-notebook`: **exit 0**; notebook, exported-policy evaluation, full test suite and actual ASGI API checks. [acceptance.log](acceptance.log), [results.json](results.json).
- Full `python -m pytest backend/tests -v`: **158 PASS, 0 FAIL, 0 skipped**, 8 existing deprecation warnings. [pytest.log](pytest.log). Covers MDP/reward/reset determinism, invalid action/state, terminal and truncation TD targets, small deterministic training, artifact checksum/schema/reward/action/shape validation, readonly Q, missing/corrupt policy fallback, actual RL Coordinator call, trace metadata, concurrent isolation, notebook execution, seed disjointness/selection consistency, and all prior Safety/Neo4j/PostgreSQL/ML regressions.
- Actual main-app API: question and synthetic assessment produce integrated RL COMPLETED/policy education-q-1.0 and persisted policy_version/action/decision_source. GET run matches PostgreSQL snapshot. Unsafe prescription request makes RL SKIPPED through input Safety veto. Missing-artifact app explicitly returns fallback-rule-1.0/source=fallback/POLICY_UNAVAILABLE. Four concurrent ASGI requests retain separate run/trace IDs and leave shared Q unchanged. [api_workflows.json](api_workflows.json).

No separate live HTTP network-server test claimed in Phase 06; API tests use real ASGI app/TestClient/AsyncClient with actual dedicated PostgreSQL and Neo4j services. Those temporary services were stopped after final verification; only verified Neo4j processes in the temporary test home and dedicated PG cluster were stopped.

## Measured simulator outcomes

| Policy / 300 paired held-out simulator seeds | Reward | Completion | Unsafe-context attempts | Mean length |
|---|---:|---:|---:|---:|
| Selected Q masked | 4.191833 | 0.963333 | 0 | 2.470000 |
| Selected Q unmasked diagnostic | 4.166000 | 0.963333 | 0 | 2.470000 |
| Fixed rule baseline | 4.311000 | 0.983333 | 0 | 2.036667 |

Selected training seed **11**, selected only on validation seeds 200000–200099. Held-out seeds 100000–100299, disjoint from training episode RNG seeds. Starting categorical states may overlap; held-out RNG trajectories are not a new patient population or external environment.

Across training seeds 11/29/47, masked Q reward mean 4.103778, variance across training seeds 0.003890, completion mean 0.941111. Baseline seed variance zero because baseline deterministic and evaluated on same paired scenarios; its variance across simulator scenarios is 8.504162. Baseline wins reward/completion and uses fewer steps here; no hyperparameter or baseline tuning performed to force Q to win. Synthetic comprehension/engagement/completion/reward are not health outcomes. Unsafe attempts are violations of simulator context restrictions, not medication actions (none exist). Zero observed held-out attempts does not establish global safety.

## Policy and notebook artifacts

- notebooks/04_rl_q_learning_training.ipynb: executed code and outputs, inline real figures and self-contained MDP/reward/baseline/seed descriptions. Markdown explanatory detail was expanded without modifying executed training code; then final acceptance re-executed notebook.
- artifacts/policies/education-q-1.0/q_table.npz: learned q and visits, no pickle. Shape **7938×6**, **6924 nonzero Q entries**, **2949 visited rows** in selected table. No claim every theoretical state was trained.
- artifacts/policies/education-q-1.0/manifest.json: policy/reward versions, encoder categories/order/shape, six action mapping, config, random seed partitions, selected seed, actual metrics, environment and SHA256. Selected seed metadata consistency regression guards against plotting-variable overwrite.
- experiments/results/phase06/: training_history.csv (24,000 real episodes), evaluation.json (all three training seeds), exported_policy_evaluation.json, exported_policy_metrics.csv.
- experiments/figures/phase06/: reward_curves.png, success_actions.png, q_table.png — actual learning/held-out plots, no fabricated metrics.
- docs/rl_mdp.md, docs/rl_experiments.md and ADR 0005. Complete source/config/docs file list: [files.txt](files.txt). Artifacts locally present and gitignored; notebook recreates them.

## Serving and MAS behavior

Default API registry replaces RL stub with integrated agent; app-owned lazy PolicyService validates exact metadata/version/checksum/dtype/shape/finiteness/visit counts and makes arrays read-only. Requests never train, fit or step simulator. Action is one of six educational interactions. Invalid encoder state, unvisited rows or absent/incompatible artifact uses explicit safe baseline fallback, separately versioned. Failed artifact load cached until restart; no older-Q search or random fallback.

State maps actual available model output band and evidence count; knowledge/engagement default medium are clearly labeled SIMULATED_DEFAULTS_NOT_MEASURED, not measured/inferred personal traits. Only one next-step recommendation per run, not a real adaptive multi-turn learner. Education uses recommendation through controlled templates and source checks; if source-based interaction lacks actual evidence, it requests clarification rather than fabricate an exchange. Trace recommendation does not assert the user completed an intervention.

Safety input/output gates and independent mandatory policy remain authoritative. Prior synthetic unsafe-RL action veto regression passes; output veto redacts recommended action and state as well as unsafe text/evidence. Prediction score is not clinical probability, RL reward is not health utility.

Runtime explicitly 2.3 for internal RL simulated context and trace policy/action/source; RLDecision v1, PredictionResult 1.1 and SafetyDecision 1.1 unchanged. Stored older versions follow existing explicit legacy-review response, no invented historic RL decisions/backfill or SQL DDL changes. ADR 0005 documents migration. Historical stub registries retained only for explicit prior-phase fixtures; default integrated app uses trained policy.

## Issues resolved and remaining limits

During metadata audit, plotting loop reused `seed`, so manifest initially recorded the last training seed while Q/report selection was seed 11. Corrected export to selected[1], added a validation-selection consistency test, and reran the entire notebook, evaluation, full suite and API verification. Final table/manifest/report now agree on seed 11; no metric fabricated or source Q substituted.

Notebook emitted existing Windows Jupyter event-loop/kernel permission/TCP warnings; all cells executed with no errors. Full pytest warnings are existing TestClient/httpx and Alembic config deprecations. No hidden skips.

Handcrafted MDP/reward probabilities, small categorical model and simulated default levels limit transfer; baseline superiority retained. Policy masks and Safety are hard guards, not learned clinical safety proof. Artifact hashes detect corruption, not authenticity; trusted deployment files required. No patient health outcomes, diagnosis/prescribing/dose action, real user knowledge estimation or clinical validation. Existing synchronous DB/retrieval throughput/auth/retention limits remain. No Phase 07 work or frontend work. No Git commit/push (repository not initialized), commit hash none.
