> Remediation completed: see [fixes_report.md](fixes_report.md). The blocked review below is preserved as historical before-state evidence.

# Technical review — Phase 06

**BLOCKED_NEEDS_FIXES**. Reviewed UTC: 2026-11-02T08:59:24.588188+00:00. No Phase 07 work; no runtime/source fixes. Review evidence and reruns only, plus phase_status review annotation. Acceptance basis: user Phase 06 requirements (notebook/learned Q/figures/evaluation/baseline/real agent/Coordinator/Safety/trace) and AGENTS.md.

## Findings, ordered by severity

**Critical:** none confirmed in the reviewed scope. This is not a security/clinical certification.

**High — H1: missing whitelist enforcement at RL→Coordinator/Safety boundary.**

`schemas/contracts.py:55` allows arbitrary action strings. Coordinator accepts completed RL outputs (`mas/coordinator.py:60`) and passes action to Safety (`:156`); `rules/engine.py:66` only rejects selected substrings. A synthetic faulty/injected RL agent returned `START_METFORMIN` (outside six education actions): actual workflow finished DEGRADED, returned that action in agent output/trace, Safety input ALLOW and output ALLOW_WITH_WARNING/E03_NO_EVIDENCE. Evidence: [invalid_action_safety_probe.json](invalid_action_safety_probe.json). This is a reproducible defense-boundary gap, not a claim that current trained Q or an ordinary HTTP input can produce this action; current PolicyService itself constrains actions. It contradicts the stronger invariant that an invalid RL result cannot escape Safety. Require action allowlist validation before accepting/forwarding results, fail closed/redact rejected actions, regression with multiple unsupported medication actions; version the output contract if changed. **Blocking.**

**High — H2: evaluation does not execute the serving policy's fallback behavior.**

`rl/experiments.py:14–22` selects argmax directly over Q; `rl/policy.py:72` falls back to baseline on unvisited rows. Replayed both on identical 300 held-out seeds: evaluator reward 4.191833/completion 0.963333 vs actual PolicyService.choose reward 4.276000/completion 0.970000. Five fallback decisions choose a different action; examples saved in [policy_evaluation_parity.json](policy_evaluation_parity.json). Original values are real raw-Q benchmark results, not fabricated; they are insufficient to characterize actual deployed policy. Selection and reported deployment metrics should use one shared decision implementation (mask + visited-state fallback), while retaining explicitly labeled pure-Q diagnostics. Add parity tests, rerun validation selection/evaluation/export and update metrics before approval. **Blocking for deployment-policy evaluation acceptance.**

**Medium — M1: recommended versus rendered action not represented separately.**

`rl/rendering.py:12` converts source-based actions without evidence into clarification, but RLDecision/trace keep the proposed action. Actual API assessment case proposes ASK_COMPREHENSION_QUESTION and responds with clarification. This fallback is documented, so not an undeclared clinical action, but trace cannot tell the effective interaction from structured fields. Add proposed/effective action and override reason, or align action eligibility/rendering. Evidence: api_workflows.json, rendering.py. Does not by itself invalidate the raw-Q simulation study; it limits simulator-to-runtime interpretation.

**Low — L1: notebook stdout still prints incorrect selected seed.**

`rl/experiments.py:61` prints loop variable seed=47 after plotting, although manifest/report correctly select seed=11. Confirmed original and rerun notebook output; [notebook_seed_output.json](notebook_seed_output.json). Earlier metadata fix corrected artifact but missed print. Fix display to selected[1] and rerun notebook output. Artifact Q and stored selection remain correct/reproducible.

**Low — L2: frontend still announces Phase 01 and no integrated model/knowledge/RL.**

`frontend/src/main.tsx:16,19` contradicts backend Phase 06. Build succeeds, but capability messaging is stale. Update status text in a separately authorized fix; no frontend source edited in this review.

## Acceptance matrix

| Phase 06 criterion | Result | Fresh evidence |
|---|---|---|
| Training notebook executes start-to-finish | PASS | Isolated copy, nbconvert exit 0, notebook.log |
| Q-table genuinely learned | PASS | Re-training exactly reproduces q and visits; shape 7938×6, 6924 nonzero Q entries |
| Actual curves and held-out simulator metrics | PASS for raw-Q experiment; FAIL for serving-policy parity | Three figures, real metrics, H2 probe |
| Fixed baseline comparison | PASS for simulator/raw-Q scope | Paired seed evaluation, baseline reward 4.311 > raw selected Q 4.191833; no forced win |
| Agent loads exact notebook-trained artifact | PASS | Both artifact checksums valid; re-trained arrays identical; API integrated policy version 1.0 |
| Coordinator actually invokes RL | PASS | api_workflows.json with COMPLETED/integrated + source=policy |
| Safety veto / action validity invariant | FAIL | Known prescription and existing tests veto; unsupported action H1 escapes boundary |
| Trace policy_version/action/decision_source | PASS for proposed decisions | Fresh API snapshots; effective-rendered action ambiguity M1 |
| Missing/invalid state/artifact explicit fallback, isolation | PASS | Full suite and actual fallback/concurrent API checks |
| Prior-phase regression tests and frontend compilation | PASS for existing tests | 158 passed/0 skipped; npm build exit 0; probes expose uncovered defects |
| Current external source-page availability, clinical utility, browser interactions | NOT_VERIFIED | Cached provenance audit only; no clinical or browser test claimed |

## Commands rerun and preservation

To preserve accepted artifacts, copied project source/data/artifacts into `.tools/review-phase06`, excluding caches/node_modules/tools/reviews. In isolated project executed:

```powershell
python scripts/check_phase06.py --execute-notebook
```

Used existing dedicated disposable PostgreSQL databases and dedicated Neo4j graph, not external production data. Actual results: **158 tests PASS, 0 FAIL, 0 skipped**, 8 known deprecation warnings; notebook/evaluation/API/fallback/Safety/concurrency checks exit 0. Logs copied to this review directory: [rerun.log](rerun.log), [pytest.log](pytest.log), [notebook.log](notebook.log), [evaluation.log](evaluation.log), [results.json](results.json). Green existing tests do not cover the two blocking review probes.

Original frontend `npm run build`: TypeScript/Vite PASS, 28 modules transformed (record: frontend_build.txt). No browser test. Original model/policy artifacts unchanged; q_table numeric arrays from isolated retraining exactly equal original, visits equal; Phase 02 ModelService checksum/load succeeds for pima-mlp-0.2.0. [artifact_verification.json](artifact_verification.json), [source_preservation.json](source_preservation.json). Main source differences from initial review copy: none. Model checkpoint and RL trained files were not overwritten by review retraining.

Metrics parity probe used original deployed PolicyService.choose and actual EducationEnv reset/step on seeds 100000–100299; no training, no fake patient/outcome data. Fault-injection probe explicitly synthetic and not installed into default application. No major fixes applied. No commit/push.

## Wiring, stubs and citations

Default main:app → api.mas.integrated_registry → actual PredictionAgent/KnowledgeAgent/RLDecisionAgent/EducationAgent/SafetyAgent. Coordinator dispatches RLTask and passes RLDecision into Education; source shows actual calls, fresh API proof confirms. Historical stub classes in agents/runtime.py, registry fixture builder and create_app(prediction_enabled=False) remain explicitly scoped to legacy/testing. Actual absent-policy fallback names fallback-rule-1.0/source=fallback; not disguised as learned policy. Availability metadata describes implementation, not proof Q artifact is ready.

Cached NIDDK provenance audit found **10 returned evidence records matching exact accessed source ID/text/URL** in new API evidence. [citation_audit.json](citation_audit.json). Not every attached evidence is cited when RL chooses a non-source interaction; no claim of complete clinical entailment or current external URL availability. No fabricated citations confirmed. No Pima correlations added to knowledge graph.

Dedicated PostgreSQL and verified temporary Neo4j Java processes stopped after review. No real patient profiles used. Original implementation report/phase milestone is not sufficient for next-phase approval while H1/H2 remain. Request separate fixes, then rerun both targeted probes and full acceptance before **APPROVED_FOR_NEXT_PHASE** can be granted.
