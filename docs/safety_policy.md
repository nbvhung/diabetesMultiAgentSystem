# Current Safety — diabetes-safety-2.0 / runtime 3.0

Source: `backend/app/research/safety.py` and Coordinator publication admission. Mandatory input/output gates detect medication/dosing requests, personal diagnosis claims, injection patterns, missing/untrusted evidence and invalid RL action. Safety may veto regardless of LLM/verifier approval; unavailable Safety fails closed. Evidence/claim admission binds source IDs, exact quote and candidate digest before final release. No dangerous personalized insulin advice is generated as a fallback.

Phase 08 actual HTTPS insulin request was BLOCKED, with no published evidence and both Safety gates in trace. Current finite software fixtures and injected faults are documented in `experiments/results/diabetes_safety.*`; historical safety-1.1 figures use different scenarios. A conditional source phrase is distinguished from a personal diagnosis in current regression tests. Rules and a same-provider semantic reviewer cannot prove universal medical safety or resistance to all prompt injection. Conflict tests alter a cited quote; they do not establish resolution of contradictory but authentic clinical guidelines.

Temporary demo access has a separate gateway password/rate/payload boundary; it does not change medical decision policy. API v1 keeps safety-1.1 for compatibility. Statements below are historical v1 context.

# Historical remediation: Safety policy 1.1 / runtime 2.4

W04 rejects actions outside the exact educational whitelist; Coordinator rejects malformed completed RL recommendations before forwarding or trace recording. Current snapshot validation prevents reintroducing such actions on GET. Proposed/effective rendering and override reason are explicit in Education output and trace. Both original gates remain mandatory. See ADR 0006 and the Phase 06 fixes report. Historical policy 1.0 notes below remain implementation history.

# Phase 06 compatibility note

RL now selects only the six educational actions from the trained synthetic simulator policy, with explicit fallback. Both mandatory safety gates and veto priority below remain active. Runtime 2.3 adds RL trace/context; SafetyDecision stays 1.1. Source/template admission now also permits the fixed nonclinical RL interaction templates described in rl_mdp.md. No RL decision can change safety policy; injected unsafe-policy tests still run. Statements below about RL being stub are historical Phase 05 context.

# Phase 05 safety policy — safety-1.0

Current rule engine executes in the MAS, independently unit-testable and deterministic. It is a software safety boundary for a local course project, not clinical diagnosis, emergency detection validation or permission to deploy with real patients. No DL retraining, RL training, additional knowledge ingestion or Phase 06 implementation.

## Mandatory workflow

```mermaid
sequenceDiagram
    participant U as Request
    participant C as Coordinator
    participant S as Safety Agent / RuleEngine
    participant A as Business agents and tools
    U->>C: Validated RunInput 2.2
    C->>S: input gate before any business dispatch
    S-->>C: Decision 1.1 + rule IDs
    alt ALLOW or ALLOW_WITH_WARNING
        C->>A: Prediction / Knowledge / RL decision / Education
        A-->>C: Typed results and candidate
    else BLOCK / ESCALATE / REQUEST_CLARIFICATION / failure
        C->>C: skip all business agents; fixed safe message
    end
    C->>S: output gate on candidate or fixed stop/referral
    S-->>C: decision, rule IDs, redacted check summary
    C->>C: latch earlier veto; redact rejected outputs
    C-->>U: terminal response + both decisions + trace
```

Every current Coordinator.run path, including explicit scaffold factories, has an input/pre-action gate and an output gate. Input BLOCK/ESCALATE/REQUEST_CLARIFICATION skips Prediction, Knowledge, RL and Education entirely; no model inference or prediction DB insert. Invalid Pydantic assessment/missing required API fields fail 422 before workflow and cannot start business actions. Missing assessment for a personal-risk request gets clarification rather than guessed values.

ESCALATE/REQUEST_CLARIFICATION are explicit SafetyDecision actions; workflow status maps to BLOCKED to preserve the workflow status enum. Emergency response is fixed generic referral to local emergency/medical support, with no diagnosis or treatment. A later output ALLOW only approves that fixed response; it never revokes the input veto. Clients must inspect safety_decisions in order, not treat only the latest Safety output as the aggregate permission.

Gate failure generates SYS01_SAFETY_FAILURE, workflow FAILED and fixed fail-closed text. If the first gate fails, output check is still attempted for the fixed failure message; no other agents run. Only Safety can re-enter RUNNING for its output pass; other terminal agents cannot be rerun. Dispatch refuses business execution before preflight, after any denial or after output check; finish requires both ordered gates and cannot label a denied run released. WorkflowResponse validation also enforces both ordered decisions and rejects COMPLETED/DEGRADED with any veto.

Coordinator independently applies the same mandatory RuleEngine conditions as a guard on injected/replaced Safety implementations. A returned weaker action is raised to the mandatory action; stricter decisions stay strict. This guard is not another clinical opinion. RL is still stub; a synthetic test action attempting insulin dosing is blocked at final gate and redacted, showing future policy actions cannot override safety. No real RL policy was trained or enabled.

## Grounding and evidence

Prediction scores are not diagnostic tests, clinical probabilities or medical evidence. A successful prediction only adds W03 research warning. Education output must be exact admitted Phase 04 source template or an approved abstention. No free-form personalized claims. Coordinator compares evidence ID, normalized text, canonical URL, source title/publisher/section against actual cached approved NIDDK documents, then checks citation ID membership. Missing cached provenance → fail closed for evidence-bearing responses. Source URL allowlisting alone is insufficient to establish a real excerpt. A generated response cannot invent an ID/quote and pass merely because it uses an official host.

Unknown citations, fabricated provenance, prompt-like retrieved content, diagnosis/dose/test-substitution claims and ungrounded additions are blocked. No-evidence/unavailable knowledge permits only explicit abstention with E03 warning. Rejected Education text is replaced by [WITHHELD_BY_SAFETY]; rejected Knowledge evidence emptied; unsafe/rejected RL action/state replaced. Numeric typed prediction may remain as an audited research result already computed after input approval, never as a diagnosis or replacement for tests. No raw rejected candidate in trace or audit. Direct internal ML/retrieval tools and read-only debug source endpoints are not public alternative clinical advice workflows; all medical-response run endpoints pass Coordinator gates.

## Explainability and privacy

SafetyDecision v1.1 adds decision (ALLOW/ALLOW_WITH_WARNING/BLOCK/ESCALATE/REQUEST_CLARIFICATION), checked_content, timestamp UTC-aware, policy_version and stage. Existing allowed/severity/rule_ids/reason retained; validator ensures allowed matches decision. checked_content contains only stage, character counts, assessment-presence and evidence count, not raw question, features or content hash. Reasons are static rule descriptions. Application logs only run/agent/status and sanitized errors. Both effective gate decisions are stored in response.safety_decisions and PostgreSQL JSON snapshot. Trace records rule_ids/safety_decision/safety_stage; raw input is not logged. Snapshot/trace still require access control before production; this phase adds no auth or retention policy.

## Contract migration

Runtime explicitly bumps 2.1→2.2 for SafetyTask context, safety audit/trace fields and response invariants. SafetyDecision v1.0 in contracts.py unchanged; policy subclass is 1.1. PredictionResult serving stays 1.1, model/data unchanged. JSON persistence means no table DDL migration needed. Prior 2.1 stored snapshots are not falsely relabeled reviewed: GET run/trace returns 409 LEGACY_RUN_REQUIRES_SAFETY_REVIEW, leaves old rows intact. Explicit old-version requests rejected 422. Current malformed snapshots without both gates fail validation and are not served. No automatic backfill or simulated historical decision. New current runs use 2.2 and contain actual decisions. See ADR 0004.

## Reproduce

```powershell
# Independent software tests; no DB needed for these:
python -m pytest backend/tests/test_safety_phase05.py -v
# Full verification requires separate disposable PostgreSQL DBs and seeded Neo4j:
$env:PHASE02_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_phase02_test'
$env:PHASE03_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_phase03_test'
$env:NEO4J_TEST_URI='bolt://localhost:17687'
python scripts/check_phase05.py
```

Full verifier rejects skipped tests, records actual fixture decisions, runs all regressions, then exercises five synthetic API cases against PostgreSQL/Neo4j with GET run/trace equality. It verifies a blocked request with complete assessment does not create a prediction and old snapshot readback is rejected. Dedicated test DBs only: previous migration regression downgrades/upgrades its disposable database.

## Limits

Structural gate enforcement is tested; semantic detection is limited to configured patterns and controlled output admission, not proof that all unsafe paraphrases are recognized. Negation, sarcasm, ambiguous context and unsupported languages can cause false positives/negatives. Emergency patterns are conservative and unvalidated; do not rely on this app to detect an emergency. Strict excerpt/template matching intentionally over-blocks novel benign education. Full source cache must be retained for provenance review; future knowledge formats need explicit policy/version/test updates. Async timeouts remain cooperative; synchronous ML/DB/retrieval work still limits throughput. API authentication, clinical review and operational rollout are not included. Phase 06 must preserve veto invariants.
