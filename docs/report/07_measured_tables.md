# BẢNG KẾT QUẢ THỰC NGHIỆM

Các bảng được đọc trực tiếp từ CSV có manifest; không lấy con số từ câu chữ của báo cáo. Timestamps/hash ở manifest là phiên bản phép đo, không tự đổi thành measurement cho mọi source code mới.

## Bảng KQ.1. Prediction trên cùng test split

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | AP |
| --- | --- | --- | --- | --- | --- | --- |
| MLP | 0.758621 | 0.709677 | 0.536585 | 0.611111 | 0.863415 | 0.781957 |
| LogisticRegression | 0.775862 | 0.777778 | 0.512195 | 0.617647 | 0.862439 | 0.783225 |
| RandomForest | 0.732759 | 0.666667 | 0.487805 | 0.563380 | 0.827967 | 0.757576 |

Nguồn: `experiments/results/prediction.csv`; manifest timestamp `2026-11-02T14:01:04.906129+00:00`; seed `42`. Scope: Restricted historical Pima cohort; research only, no clinical generalization.

## Bảng KQ.2. Retrieval confirmatory phrasings

| Strategy | Recall@3 | Precision returned | MRR@3 | Provenance | Latency ms |
| --- | --- | --- | --- | --- | --- |
| lexical | 0.151806 | 0.208333 | 0.295833 | 1.000000 | 30.356368 |
| semantic | 0.313819 | 0.362500 | 0.575000 | 1.000000 | 69.531045 |
| graph | 0.293472 | 0.391667 | 0.508333 | 1.000000 | 30.587655 |
| hybrid | 0.290972 | 0.570833 | 0.625000 | 1.000000 | 1009.579682 |

Nguồn: `experiments/results/diabetes_rag.csv`; manifest timestamp `2026-11-02T17:28:32.920377+00:00`; seed `42`. Scope: 125 project-authored SYNTHETIC questions; 40 confirmatory phrasings fixed after architecture selection. Coarse target source-section relevance, not clinical correctness.

## Bảng KQ.3. Offline MAS/direct, khác retry budget

| Method | Runs | Completion | Evidence relevance | Safety invariant | Latency ms |
| --- | --- | --- | --- | --- | --- |
| single_workflow | 44 | 0.727273 | 0.750000 | 1 | 435.450548 |
| multi_agent | 44 | 0.863636 | 0.650000 | 1 | 593.688205 |

Nguồn: `experiments/results/diabetes_mas.csv`; manifest timestamp `2026-11-02T17:29:48.696880+00:00`; seed `42`. Scope: Real orchestration, actual Neo4j + semantic retrieval; LLM explicitly disabled in both methods. This is not an evaluation of generated LLM answer quality.

## Bảng KQ.4. Policy trên cùng simulator evaluation seeds

| Policy | Avg reward | Completion | Reward variance | Unsafe attempts |
| --- | --- | --- | --- | --- |
| q_learning | 4.276000 | 0.970000 | 8.358457 | 0 |
| rule_based | 4.311000 | 0.983333 | 8.504162 | 0 |

Nguồn: `experiments/results/rl.csv`; manifest timestamp `2026-11-02T14:01:51.244914+00:00`; seed `300 fixed evaluation seeds, 100000..100299; full list in manifest`. Scope: SYNTHETIC educational simulator only; not patient health or measured learning outcomes.

## Bảng KQ.5. Current finite safety expectations

| Layer | Cases | Passed | Pass rate |
| --- | --- | --- | --- |
| actual_coordinator_fault | 2 | 2 | 1 |
| actual_workflow | 8 | 8 | 1 |
| rules | 4 | 4 | 1 |

Nguồn: `experiments/results/diabetes_safety.csv`; manifest timestamp `2026-11-02T17:30:13.487241+00:00`; seed `42`. Scope: Software safety regression; simulated conflicting quote probes provenance, not general medical conflict reasoning. No live LLM safety claim.

## Bảng KQ.6. LLM summary, acceptance có điều kiện

| Questions | LLM outputs | Conditional acceptance | Latency ms | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- |
| 6 | 3 | 1 | 2278.704033 | 4477 | 694 |

Nguồn: `experiments/results/diabetes_llm.csv`; manifest timestamp `2026-11-03T08:30:44.253290+00:00`; seed `42`. Scope: Actual remote LLM calls. Automated verifier acceptance is not clinical accuracy; approved responses require further human source review.

## Bảng KQ.7. Toàn bộ sáu câu LLM benchmark

| Question ID | Language | Mode | Accepted | Provider error |
| --- | --- | --- | --- | --- |
| definition:confirmatory:0 | vi | clarification | 0 | — |
| definition:confirmatory:1 | en | llm | 1 | — |
| symptoms:confirmatory:0 | vi | clarification | 0 | — |
| symptoms:confirmatory:1 | en | llm | 1 | — |
| risk:confirmatory:0 | vi | extractive | 0 | GROQ_STRUCTURED_OUTPUT_REJECTED |
| risk:confirmatory:1 | en | llm | 1 | — |

Nguồn: diabetes_llm_rows.csv. Accepted coverage 3/6; 3/3 chỉ là acceptance có điều kiện trên generated outputs. Non-generation không bị loại khỏi bảng.
