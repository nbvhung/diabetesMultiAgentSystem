# Pima dataset — research data card

Source CSV: https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv
Mirror page: https://github.com/jbrownlee/Datasets/blob/master/pima-indians-diabetes.data.csv
Original dataset description: https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.names

Downloaded 2026-11-02; SHA256 `6bfe5d0f379d17a0e0819b996407e3c09bf80febd4287f2ed212190dfff154af`. Downloader pins this checksum: changed source requires review. Original owner identified in .names: NIDDK; donor Vincent Sigillito; received 9 May 1990. Reference: Smith et al. (1988), Using the ADAP learning algorithm to forecast the onset of diabetes mellitus, SCAMC.

License: no explicit dataset license was verified in the mirror or supplied .names. Do not infer CC0/CC-BY from unrelated replications or apply a repository code license to data. For course research with attribution; redistribution/commercial rights remain unverified. Raw CSV and fitted patient-derived preprocessing/checkpoints remain gitignored. This historical dataset is NOT synthetic; demo_cases database accepts only synthetic records. No raw patient rows are displayed in notebooks or inserted into DB.

Verified 768 rows, 8 numeric features plus binary Outcome; 500 negatives, 268 positives. Population: females of Pima Indian heritage, age at least 21, near Phoenix Arizona. This restricted historical sample does not represent all ages, sexes, ancestries or clinical settings. Outcome reflects historical study definitions, not a universal prospective risk endpoint.

Data dictionary in notebook 01 follows .names order: pregnancies count, 2h oral glucose mg/dL, diastolic BP mmHg, triceps skinfold mm, 2h insulin microU/mL, BMI kg/m², pedigree index, age years. Outcome 0/1 is negative/positive study label.

Zero in glucose/BP/skinfold/insulin/BMI is treated as missing. Pregnancy zero remains valid. Train-only median imputation and StandardScaler; no rows dropped or synthetic oversampling. EDA aggregates/full-data plots are descriptive, not feature selection; preprocessing rule fixed in advance. Class-stratified seed 42 split: train 537 (187 positive), validation 115 (40 positive), test 116 (41 positive). Disjoint complete indices exported, no target included in features. No patient/group identifiers are available: row-level split cannot establish person-level independence across possible repeat visits.

Split indices: experiments/results/phase02/splits.json; preprocessing config and dataset digest in artifacts/models/pima-mlp-0.2.0/. Re-run download and notebooks via README. No alternative synthetic dataset will be substituted if source is inaccessible.
