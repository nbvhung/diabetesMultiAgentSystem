# Phase 08 verification note

Current serving artifact remains `education-q-1.1`, loaded successfully during Phase 08 initialization and the synthetic HTTPS assessment workflow. No Q-table training/update was performed in Phase 08. The MDP and saved simulator measurements below are unchanged; runtime context defaults are simulated, not inferred patient understanding. [Current agent design](agent_design.md), [verification](validation/phase08/report.md).

# Phase 06 — synthetic educational MDP

RL is a supporting MAS decision tool, never a diagnosis, prescription, medication/treatment or dosing optimizer. Simulator rewards/task completion do not represent real health improvement. No patient trajectories or synthetic data represented as real people. No online learning in requests.

## State and action encoding

State tuple order is locked in artifact metadata:

| Field | Encoding |
|---|---|
| prediction_band | 0 unavailable; 1 lower-score; 2 higher-score (runtime threshold 0.5 only, not a clinical threshold) |
| knowledge | 0 low / 1 medium / 2 high; SIMULATED |
| engagement | 0 low / 1 medium / 2 high; SIMULATED |
| evidence | 0 none / 1 partial / 2 sufficient; synthetic in env, runtime maps counts 0/1–2/3+ |
| safety | 0 normal / 1 restricted |
| previous_action | 0–5 corresponding to actions below, 6 NONE at reset |
| remaining | 0–6 interaction budget; reset=6 |

Shape (3,3,3,3,2,7,7), 7,938 discrete states; numpy.ravel_multi_index row encoder. Previous action is necessary for Markov repetition penalty; remaining budget makes finite horizon explicit. Every reset independently samples five initial categorical values uniformly, then appends NONE and budget six, unless explicit scenario is supplied. Same seed and actions give identical outcomes through a per-environment numpy Generator. Environment state never shared between requests.

Actions 0–5, exactly:

1. EXPLAIN_PREDICTION_LIMITATIONS
2. PROVIDE_GENERAL_EDUCATION
3. SHOW_EVIDENCE
4. ASK_COMPREHENSION_QUESTION
5. REQUEST_CLARIFICATION
6. SUGGEST_CLINICIAN_DISCUSSION

No medication or clinical-treatment action. Invalid indices/strings outside action mapping raise ValueError. Runtime policy mask allows only clarification/referral when restricted and excludes general education/evidence display when evidence absent. Same restrictions respected by baseline. Unsupported contextual educational attempts may occur during simulated exploration to learn penalties; this is not real treatment experimentation.

## Transitions

reset(seed,options) returns observation/info; step returns observation/reward/terminated/truncated/info. Random draws are simulated transition assumptions, not estimates from users.

- Explain limitations with prediction present: knowledge increases with probability .8.
- General education/display evidence with evidence present: knowledge increases with probability .65/.8; engagement increases with probability .45.
- Comprehension question: engagement increases with probability .75. Education completes only if pre-action knowledge=high, engagement>=medium and evidence exists.
- Clarification: evidence and engagement each can increase with probability .7/.5. Evidence arriving here is a simulated response, never invented retrieval in the actual app.
- Clinician discussion: terminates episode; counts as appropriate completed handoff only when restricted, not a real referral outcome.
- Restricted disallowed action: unsafe-context penalty and no learning transition. Education/show without evidence, or explain without prediction: unsupported penalty and no learning transition.

Knowledge/engagement/evidence saturate at 2; band/safety fixed during episode. Action history and budget always update. Termination is completion/referral; truncation when budget reaches zero. Calling step after done raises. Module split: rl/mdp.py (state/transition), rl/reward.py (proxy reward), rl/learning.py (algorithm).

## Reward version education-reward-1.0

Unsafe restricted action: -20. Otherwise -0.2 step cost +1.5*knowledge gain +0.5*engagement gain; -4 unsupported context; -0.75 repeated action; +0.3 evidence-supported general/show; +6 normal educational completion or +2 restricted appropriate handoff; -1 for normal-state clinician discussion (valid but does not finish educational task). Repetition penalty applies to any immediately repeated action, a deliberate simplifying assumption. No health outcome or clinical utility claim.

## Q-learning and experiments

Q starts zero; epsilon-greedy training explores all six educational actions. Bellman update uses alpha=.15, gamma=.95. epsilon=max(.05,1*.9994**episode). Terminal OR finite-budget truncation target equals reward; no bootstrap, because remaining budget is in state. Other target is r+gamma*max(Q(next)).

Three training seeds 11/29/47, 8,000 episodes each. Episode simulator seed = training_seed*1,000,000 + episode. Validation seeds 200000–200099; held-out 100000–100299, disjoint from all training seeds/scenarios. Select policy by highest validation serving-policy reward, including masks and unvisited-state fallback, deterministic tie-break smaller training seed. Held-out results not used for selection or baseline adjustment.

Baseline rule before evaluation: restricted→clinician; no evidence→clarify; high knowledge+engagement→comprehension; low engagement→comprehension; present prediction and low knowledge→explain limitations unless repeated; sufficient evidence→show unless repeated, else general education. Baseline not deliberately weakened or tuned after Q results. Both baseline and Q share same simulator seeds and finite budget. Report masked deployment Q and unmasked diagnostic Q separately.

## Runtime mapping and safety

Main API registry uses integrated RLDecisionAgent with app-owned lazy PolicyService. Input from Coordinator after preflight and Prediction/Knowledge. If no evidence/prediction, real RL still runs to choose a clarification/next interaction, unlike historical stub routing. Prior explicit scaffold registry stays stub for legacy tests. Production path uses the trained policy.

Runtime knowledge/engagement default to medium and are clearly tagged SIMULATED_DEFAULTS_NOT_MEASURED. No real individual knowledge/engagement inferred, no demographic feature used for these levels. Initial runtime previous_action=NONE, remaining=6; this phase selects one next action per run, not a durable multi-turn learner or real simulator rollout. Prediction band is actual model output category when available, not a diagnostic risk group. Evidence count is actual retrieved evidence. Preflight warning maps restricted; denied input never calls RL.

Education uses action to select fixed limitations/clarification/clinician-discussion prompts, source template display/general education, or source template plus comprehension question. No new medical claims. Coordinator admits only these exact templates or the original source-excerpt template, preserving provenance and two Safety gates. Source-bearing responses still require exact approved corpus metadata. Neither policy action nor Q value grants clinical permission. Phase 05 post gate can veto actions, including injected synthetic dosing actions; veto redacts recommendation/action and trace action value.

## Artifact safety and fallback

artifacts/policies/education-q-1.1/q_table.npz contains numeric q and visits (no pickle). manifest.json includes format/policy/reward version, state values/order/shape, action mapping, config, train/validation/test seeds, selected seed, actual evaluation aggregates, environment versions, SHA256. Loader validates Pydantic schema, exact encoder/actions/version, checksum, expanded ZIP size, numeric dtype/shape/finiteness and visit counts. q/visits readonly; no fitting, updates or environment stepping in requests. Checksums detect corruption, not malicious authenticity: deploy trusted artifacts.

Missing/corrupt/incompatible artifact yields explicit baseline fallback: decision_source=fallback, policy_version=fallback-rule-1.0, decision_reason=POLICY_UNAVAILABLE. Outside encoder domain → REQUEST_CLARIFICATION/INVALID_STATE; valid but unvisited row→baseline/UNVISITED_STATE. Never claim these came from learned Q. Failed load cached until restart; no silent previous-version lookup. Trace records policy_version/action/decision_source plus proposed_action/effective_action/action_override_reason. Shared model/table are app-owned, all run state request-local.


Renderer guard: if a proposed general/show/comprehension interaction has no actual source evidence, Education requests topic clarification instead of pretending evidence was supplied. Policy recommendation remains in trace; it is not a claim the educational intervention was completed. This is an Education evidence fallback, distinct from policy-service fallback decision_source.


## Technical review corrections (current)

ADR 0006 supersedes the prior raw-Q-only evaluation: validation and held-out serving metrics now use exactly the selector called by PolicyService.choose, including visited-state fallback. Raw unmasked Q remains a diagnostic comparison only. Metadata includes manifest format 1.1 / evaluation_policy=serving-policy-fallback-v1. Current runtime 2.4 and Safety policy 1.1 reject any noncanonical RL action before Education or public serialization. Proposed and effective action are both persisted; evidence-driven rendering override has a structured reason. No DL, reward, simulator transition or baseline changes.
