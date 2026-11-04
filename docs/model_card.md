# Current serving status — Phase 08

The frozen model is integrated into Prediction Agent, runtime 3.0/v2, with PostgreSQL persistence for synthetic inputs. Native loader/inference and authenticated HTTPS demo were verified in Phase 08; Docker image execution remains blocked by the missing host engine. No model training/threshold/calibration change was made. The card and measured training results below describe the original training run; they are not a new Phase 08 training experiment.

# Model card — pima-mlp-0.2.0

Offline research MLP, now served by Prediction Agent; not a clinical diagnosis or validated general-population risk calculator. Its synthetic assessment output is an educational demonstration of model-assisted orchestration.

PyTorch CPU MLP 8→32→16→1, ReLU, dropout 0.15; BCEWithLogitsLoss; Adam lr 0.001, batch 32, max 200 epochs, early stopping patience 20/min_delta 1e-5. Seed 42; deterministic CPU algorithms. Executed 44 epochs; checkpoint epoch 24 selected by minimum validation BCE, not test performance. Threshold fixed at 0.5 in advance. Median imputer and StandardScaler fit on train only. No SMOTE, tuning on test, or calibration fitting on test.

Dataset/source/license caveats: [data card](data_card.md). Train/validation/test 537/115/116, stratified and disjoint; test has 41 positive/75 negative. These are single-split estimates, no confidence interval or external validation. Baselines LogisticRegression(max_iter=2000) and RandomForest(300 trees,min_samples_leaf=2) fit identical training data/transforms, same test, no test-driven selection.

## Actual held-out results

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC (AP) | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| MLP | 0.758621 | 0.709677 | 0.536585 | 0.611111 | 0.863415 | 0.781957 | 0.151729 |
| LogisticRegression | 0.775862 | 0.777778 | 0.512195 | 0.617647 | 0.862439 | 0.783225 | 0.149270 |
| RandomForest | 0.732759 | 0.666667 | 0.487805 | 0.563380 | 0.827967 | 0.757576 | 0.161513 |

PR-AUC here means sklearn average_precision_score, not trapezoidal PR integral. Scores are uncalibrated. Brier/reliability plots with five quantile bins assess calibration without fitting it. Small bin sizes make calibration estimates unstable. LR has higher accuracy/F1 and lower Brier than MLP on this split; MLP has marginally higher ROC-AUC. No universal superiority claim or significance claim is warranted. Training overfit is controlled by validation early stopping, not eliminated.

Error counts (no raw patient rows): MLP: FP=9, FN=19; LogisticRegression: FP=6, FN=20; RandomForest: FP=10, FN=21. False negatives show that this classifier misses substantial positive labels at threshold 0.5; false positives also occur. Do not use score/threshold for clinical decisions. No subgroup fairness or person-level repeat-visit validation possible from available identifiers. Historical female Pima cohort cannot justify general-population use.

## Artifacts and integrity

`artifacts/models/pima-mlp-0.2.0/`: checkpoint.pt, preprocessing.joblib, preprocessing_config.json, training_config.json, manifest.json. Manifest includes SHA256 of four artifacts, dataset SHA256 and environment versions. Loader verifies hashes then uses torch.load(weights_only=True). Only trusted local joblib artifacts should be loaded; checksums are not cryptographic signatures. Fitted artifacts and raw CSV remain gitignored; present locally as deliverables, not committed.

`experiments/results/phase02/`: metrics.csv/json, learning_history.csv, splits.json, split_summary.json, environment.json, per-model error indices. `experiments/figures/phase02/`: feature distributions, correlation, learning curves and three evaluation panels (confusion/ROC/PR/calibration), 6 PNGs total.

Reproduction and DB migration commands: [installation](installation.md), [original training procedure](phase02_reproduce.md). Original training evidence: [Phase 02 report](validation/phase02/report.md). Current integration evidence: [Phase 08 verification](validation/phase08/report.md). No clinical validation is claimed.
