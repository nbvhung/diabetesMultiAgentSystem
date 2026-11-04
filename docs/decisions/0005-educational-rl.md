# ADR 0005 — offline educational Q policy and runtime 2.3

Accepted for Phase 06, 2026-11-02. No clinical/dosing policy, no DL changes.

Implement tabular Q-learning in custom seeded finite educational MDP with previous action and remaining budget to make reward/horizon Markov. Use actual executed Jupyter notebook as training deliverable. Validate against a fixed reasonable rule baseline on paired held-out simulator seeds; keep results even when baseline wins. Three training seeds; select on separate validation seeds only. Synthetic reward/task completion are not clinical outcomes.

Numeric NPZ and strict JSON manifest chosen over pickle. App-owned PolicyService lazy loads once, validates hash/version/action/schema/shape and keeps arrays readonly. Absent/incompatible policy, out-of-encoder or unvisited state gets explicitly versioned baseline fallback, never retraining or disguised Q result. Safety masks reduce context-invalid actions but cannot replace mandatory Phase 05 veto.

Add typed simulated context to RLTask (knowledge/engagement defaults medium, safety status from preflight); trace metadata policy_version/action/decision_source. Runtime wire schema 2.2→2.3, explicit version change with tests. RLDecision v1 remains unchanged; its state JSON contains clear simulated context and fallback reasons. Current DB snapshots use 2.3; older versions rejected through existing legacy-review response instead of silently relabeled. No JSON backfill/DDL needed; existing tables/transactions used. Snapshot contract migration is separate from clinical revalidation; historic records are not retroactively assigned an RL decision.

Main app integrates actual RL agent and calls it even when evidence/prediction absent so clarification can be chosen; historical stub fixture registry unchanged. Education action rendering uses a single fixed template renderer; Coordinator compares the same renderer to preserve output admission. Phase 05 input/output gates and independent minimum-policy enforcement unchanged. New action/decision trace fields are redacted on veto. Model weights, Neo4j corpus and safety clinical patterns not changed.

Limits: simulator handcrafted, not real user modeling; default simulated levels cannot personalize a patient's education. One action per run, no persistent online policy updates or multi-turn state adaptation. Learned and baseline results measure only this simulator. Consider real nonclinical interaction design and review in future explicitly authorized phases.
