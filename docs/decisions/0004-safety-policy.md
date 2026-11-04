# ADR 0004 — mandatory two-stage safety and runtime 2.2

Accepted for Phase 05, 2026-11-02.

Prior output-only lexical safety could execute prediction before detecting an unsafe request. New versioned RuleEngine has immutable metadata and five rule groups. Default SafetyAgent is integrated in all current registries; old minimal class is retained only as LegacySafetyAgent history, and current Coordinator refuses unversioned/invalid safety decisions. Before business dispatch and before final release, Safety runs; veto latches across stages and cannot be weakened by RL or later ALLOW. Mandatory engine independently enforces lower bounds on a replaced agent's decision.

Schema changes: new safety.py Decision subclass v1.1; untouched contracts.py v1.0 and PredictionResult 1.1. Runtime 2.2 includes contextual SafetyTask, rule IDs/effective decisions in trace, both safety_decisions in state/response. Extra fields/new semantics are an explicit wire update, not silently added under 2.1. Existing clients should omit version for current default or send 2.2 and understand both ordered gates. Enum workflow BLOCKED also represents escalation/clarification, distinguished by actual SafetyDecision. No clinical status label introduced.

No SQL DDL migration: existing JSON snapshot columns store new versions. Legacy stored snapshots never acquired new safety checks retroactively; GET rejects them with 409, not automatic fabricated migration. Current response validation requires the two-stage audit. Historical rows remain for separate offline review; production backfill requires approved policy-aware process.

State transitions: only Safety may re-enter RUNNING once for output check after an input decision. The input and output trace events have independent message IDs. Effective gate audit includes built-in failure decisions for unavailable/timeout/exception, no raw content. Rule IDs are persisted in each gate event JSON. Clinical tool ordering remains sequential, preflight now precedes any business tool.

Evidence admission checks full actual cached provenance and exact template, rather than trusting URL strings or a source ID invented by an agent. This is deliberately restrictive and can reject benign new responses. No LLM judge/clinical model in safety. Rules describe software safeguards, not full medical validity.

Tests from earlier phases updated only for intentional new semantics: two dispatches, preflight SKIPPED instead of post-hoc redaction, citation veto BLOCKED, out-of-scope preflight vs true no-evidence retrieval, explicit 2.2, manual dispatch now needs approved preflight. Historical data/model tests still run. DL weights, preprocessing, retrieval corpus and RL remain unchanged.
