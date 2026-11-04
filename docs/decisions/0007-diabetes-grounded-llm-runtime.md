# ADR 0007 — Diabetes-grounded LLM and feedback-agent runtime

Status: implemented; live Groq validation is a separate credential-dependent gate. The user authorized this expansion after reviewing Phase 07, before Phase 08. This is not Phase 08 packaging/deployment.

## Problem

Runtime 2.4 coordinated five agents but Education emitted fixed templates/excerpts. Its knowledge corpus was one NIDDK overview page with 19 sentence chunks and lexical hashing. The original small benchmark measured provenance separately from relevance; passing integration tests did not establish a capable diabetes conversational assistant. A new requirement explicitly includes an LLM, wider diabetes knowledge and stronger multi-agent feedback.

## Decision

Introduce runtime **3.0** under **`/api/v2`**, with separate schemas, registry, Coordinator and transaction repository. Preserve `/api/v1` runtime 2.4, frozen base contracts 1.0, model serving 1.1, educational policy 1.1 and their regression checks. No silent field/version mutation. The frontend now uses v2; v2 GET accepts either a validated 3.0 snapshot or the original unmodified 2.4 snapshot. Other historical schemas still require explicit review. Existing JSON SQL columns store 3.0; no DDL or fake migration of old runs.

The six role contracts are Prediction, Knowledge, RL, Education, Evidence Verifier and Safety. Coordinator owns request-local messages/state, routing, per-agent timeout, up to two retrieval rounds, two composition attempts, a maximum of four remote calls, controlled fallback and finalization. Safety runs before business dispatch and at final publication, and its mandatory deterministic policy is independently enforced even if an agent returns a weaker decision.

Knowledge combines fixed Neo4j reads over a namespaced corpus release, a prepared multilingual sentence encoder, lexical retrieval, topic constraints and a prepared cross-encoder reranker. Every result maps to a versioned source snapshot. Models run on CPU; requests do not download or train anything. Missing semantic/reranker artifacts produce declared fallback, not manufactured vectors. Missing graph never silently uses the local corpus as if Neo4j retrieval succeeded.

Education calls Groq through one restricted structured-output adapter. It receives only a redacted question, approved evidence and a whitelisted educational action; no raw assessment/features, secret or arbitrary tool permission. Returned JSON consists of atomic claims and exact supporting quotations/IDs. A separate Verifier call checks support, contradiction, population/type, numbers and relevance. Local checks enforce source admission, quote containment, citation sets, numeric support and rendered-text equality. Coordinator repeats deterministic publication admission independently. A verifier boolean from the author, client, or an invalid agent output cannot waive these checks.

If Groq is unavailable or a draft remains unverified, publish only independently checked source excerpts or a controlled clarification, with `generation_mode`, provider status/error and warnings. Never report that fallback as generated LLM success. Rejected prose/quotes are erased from released agent outputs; trace retains only codes/counts/approved metadata. Input/output Safety failure withholds content. A semantic reviewer is fallible and is not a clinical certification mechanism.

`diabetes-safety-2.0` reuses the rule categories while distinguishing a sourced conditional “If you have diabetes…” from a categorical personal diagnosis. Type-specific categorical diagnoses are still blocked. Historical `safety-1.1` is unchanged. The new version has separate regression checks.

## Tool rights and persistence

| Agent | Allowed tools | Fallback |
|---|---|---|
| Prediction | Existing frozen PyTorch inference and synthetic SQL prediction write | UNAVAILABLE for missing artifact; SQL failure rolls back |
| Knowledge | Fixed diabetes Neo4j reads; local corpus/embedding/reranker | Declared unavailable or weak-evidence clarification |
| RL | Existing local educational Q-policy | Explicit named rule fallback |
| Education | Groq structured diabetes composition | Labeled source quotes/clarification |
| Verifier | Cached source admission; separate Groq evidence review | Reject unverified draft |
| Safety | Versioned deterministic rules | Fail closed |

New rights apply only to the new explicitly versioned registry; Phase 00 enabled_tools and historical registry contracts are untouched. No user-provided Cypher, arbitrary URLs, code execution, browser search or unrestricted model tools. PostgreSQL stores run/prediction/events atomically; raw question/assessment do not enter trace. Actual prediction features are persisted only for explicitly confirmed synthetic assessments, as before.

## Evaluation and compatibility consequences

Freeze the trained DL/RL files, record before/after hashes, run all legacy regression checks and new fault/grounding checks. New experiment bundles have their own names; old metrics are historical and never relabeled for the larger corpus. Compare same-tool single-workflow and MAS behavior; LLM-disabled measurements are labeled and cannot establish generated-answer quality. Live LLM metrics require actual remote responses. Missing credentials result in NOT_RUN/null quality metrics, not simulated model scores.

Local testing needs dedicated disposable PostgreSQL/Neo4j. A one-time source/model warmup occurs outside agent-task budgets and before the SQL transaction; unsafe input and out-of-scope questions do not trigger this warmup. Model loading is not a patient inference/retrieval action. Blocking model/driver work is not claimed to be fully preemptible by asyncio timeout.

Limitations: small public-source corpus, coarse source-section benchmark labels, imperfect semantic verification, no expert clinical validation, incomplete identifier redaction and no production auth/rate-limiting deployment. Runtime 3.0 is an education/research system, not diagnosis, prescription or a clinically validated patient advisor.
