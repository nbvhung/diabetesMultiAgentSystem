# Phase 06 corrected experiments — serving-policy parity

Re-executed notebook training and export after review fixes. Policy education-q-1.1, format 1.1, selected training seed 11. Three seeds × 8000 episodes, same Q-learning/reward/MDP and fixed baseline as before. Selection uses validation seeds 200000–200099 and exact serving behavior (mask plus unseen-state fallback). Held-out seeds 100000–100299 remain untouched by selection.

| Policy | Mean reward | Completion | Unsafe-context attempts | Mean length |
|---|---:|---:|---:|---:|
| Serving Q + explicit fallback | 4.276000 | 0.970000 | 0 | 2.470000 |
| Unmasked raw-Q diagnostic | 4.166000 | 0.963333 | 0 | 2.470000 |
| Fixed rule baseline | 4.311000 | 0.983333 | 0 | 2.036667 |

The q_learning entry in exported_policy_evaluation.json is calculated through the loaded PolicyService.choose callback. An exact comparison to in-memory evaluation with q+visits is asserted before exporting CSV; mismatch fails the command. Detailed episode action sequences/decision sources and fallback counts are stored, not only means. The original review mismatch was genuine and the old metrics remain in historical review evidence; they must not be relabeled as corrected serving metrics.

Current selected serving policy: fallback count 5 on held-out trajectories. Across three training seeds, serving reward mean 4.160444, population variance 0.007104, completion mean 0.944444. Baseline reward 4.311 and completion 0.983333 remain better than the selected policy; no baseline/reward tuning performed to force a win. Unmasked raw-Q results are explicitly diagnostic and do not model runtime fallback. Counts reflect simulator restricted contexts, never clinical actions or health outcomes.

Artifacts: artifacts/policies/education-q-1.1/q_table.npz + manifest.json. Original 1.0 retained, not the current default. Numeric readonly NPZ, checksum/version/schema validation, no pickle or request-time learning. Notebook stdout, manifest and validation report all agree on selected seed. Figures: reward_curves.png, success_actions.png and q_table.png under experiments/figures/phase06, regenerated from the actual run. Results/history/metrics CSV/JSON remain under experiments/results/phase06. New acceptance logs and independent closure probes: docs/validation/phase06_fixes/.

```powershell
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/04_rl_q_learning_training.ipynb --ExecutePreprocessor.timeout=600
python scripts/evaluate_rl.py
python scripts/check_phase06.py --execute-notebook
python scripts/verify_phase06_review.py
```

Full check needs the existing separate disposable PostgreSQL URLs and seeded Neo4j test URI. No clinical utility/real user comprehension is measured. Held-out RNG trajectories can start in categories seen in training; not an external population test. Runtime selects one next interaction using explicitly simulated medium knowledge/engagement defaults, not a real adaptive multi-turn learner. See rl_mdp.md and ADR 0006 for action admission and proposed/effective trace semantics.
