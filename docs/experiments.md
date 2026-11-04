# Phase 08 — final evidence and interpretation

No historical metric was regenerated merely to make the final report look better. Prediction/RL/RAG/MAS/safety bundles below retain their own timestamps, dataset/config/source hashes. Phase 08 reran full software/integration checks and added **actual bounded Groq evaluation**: `experiments/results/diabetes_llm.{csv,json,manifest.json}` plus rows and PNG.

On six fixed confirmatory questions, three produced genuine LLM answers and all three passed the separate automated verifier. Two Vietnamese phrasings produced clarification before a provider generation, and one Vietnamese risk question fell back to exact quotes after `GROQ_STRUCTURED_OUTPUT_REJECTED`. Thus generated-and-accepted coverage is **3/6**, while verifier acceptance conditional on generated answers is **3/3**. Neither is clinical accuracy or a human medical review. Reported mean 2278.704 ms is over generated cases; token usage totals are measured metadata, not an estimate of hidden provider billing. Review the rows; do not hide non-generation cases behind the conditional 1.0.

Current native verification: 249 backend tests, 22 frontend unit tests, production build and 6 browser/API scenarios passed. A separate authenticated HTTPS demo executed three real scenarios and read their PostgreSQL snapshots back. Cloud hosting is NOT_COMPLETED; Compose runtime remains BLOCKED because the host has no Docker engine. [Final software/deployment verification](validation/phase08/report.md), [report chapters](report/README.md).

The current offline MAS comparison uses two repeats of 22 scenarios per method with shared tools but different retrieval/repair budgets; no causal decomposition advantage or LLM-quality claim. The first-pass RAG confirmatory set checks phrasings on overlapping topics, not external validation. Q-learning remains below the rule baseline on the saved simulator evaluation. Original protocols follow as historical context, with source-grounded limitations preserved.

# Historical Phase 07 — experimental protocol and measured artifacts

Current expanded-corpus/LLM/MAS work has [a separate protocol](diabetes_expansion_experiments.md) and [actual report](validation/diabetes_expansion/report.md). Historical results below use a different smaller corpus/benchmark and are not relabeled as measurements of the new system.

Các script E1–E5 ghi metric từ thực thi thật, CSV tổng hợp, CSV từng mẫu, JSON chi tiết, PNG và manifest. Không có metric mặc định trong frontend. Kết quả nằm trực tiếp tại `experiments/results/` và `experiments/figures/`, không ghi đè báo cáo lịch sử `phase02/phase04/phase06/`.

```powershell
python scripts/evaluate_prediction.py
python scripts/evaluate_rag.py
python scripts/evaluate_mas.py
python scripts/evaluate_rl.py
python scripts/evaluate_safety.py
```

E2/E3/E5 cần Neo4j thật đã seed. E3/E5 cần PostgreSQL đã migrate theo DATABASE_URL; benchmark dùng transaction rollback cho cả hai phương pháp và không giả baseline là production MAS snapshot. Bốn demo API có commit và kiểm tra GET persistence riêng. Xem demo_guide.md để cấu hình. Chạy `python scripts/check_phase07.py` để lưu toàn bộ log/return code và browser screenshots.

Kết quả đã đo của lượt xác minh Phase 07:

| Thí nghiệm | Kết quả |
|---|---|
| E1 accuracy / F1 | MLP 0.758621 / 0.611111; Logistic Regression 0.775862 / 0.617647; Random Forest 0.732759 / 0.563380 |
| E2 Recall@5 / MRR@5 | Vector 0.540833 / 0.751667; graph 0.920000 / 0.925000; hybrid 0.917500 / 0.925000 |
| E3 single workflow và MAS | Cùng completion 0.916667, relevant evidence correctness 0.520000, provenance 1.000000, software safety invariants 1.000000; không chứng minh MAS tốt hơn |
| E4 serving Q / rule baseline | Reward 4.276 / 4.311; completion 0.970000 / 0.983333; cả hai có 0 unsafe-context attempts |
| E5 expected behaviors | 41/41 rule fixtures; 13/14 workflow cases; còn safe-query false positive S04 |

Số đầy đủ gồm precision/recall/AUC, variance, latency và per-case failures nằm trong CSV/JSON và [verification report](validation/phase07/report.md). Không suy diễn clinical effectiveness từ các metric này.

## Dataset và ground truth

`experiments/configs/phase07_scenarios.json`, version `phase07-benchmark-1.0`, chứa 12 **SYNTHETIC project-authored benchmark scenarios**, không phải hồ sơ bệnh nhân. Mỗi scenario có category, câu hỏi, assessment presence, expected status, prediction/evidence presence, relevant sections và expected rule/error/fallback. Giá trị 8 features do dự án tạo chỉ để demo pipeline. Ground truth được cố định trước khi chạy; S04 safe-query false positive được giữ là failure, không sửa expected label theo output.

E2 tái dùng 24 câu hỏi Phase 04 với section relevance được gán thủ công, cùng NIDDK snapshot thật. E1 dùng bộ Pima nghiên cứu công khai đã có từ Phase 02, không phải dữ liệu bệnh nhân demo tự tạo. E4 dùng held-out simulator seeds của Phase 06. Không trộn ba loại dữ liệu hoặc gọi synthetic scenario là clinical validation.

## E1 — prediction

MLP checkpoint Phase 02 giữ nguyên; Logistic Regression (`max_iter=2000`) và Random Forest (300 cây, `min_samples_leaf=2`) fit trên cùng 537 training indices. Validation 115/test 116 giữ nguyên. Cả ba dùng preprocessing train-only đã khóa; threshold 0.5, không chọn threshold/hyperparameter bằng test. `prediction_rows.csv` ghi index/target/score/class, không ghi raw feature profile.

Accuracy, precision, recall, F1, ROC-AUC và PR-AUC được tính trên cùng test split. PR-AUC được định nghĩa là average precision. Các metric không chứng minh tính phù hợp lâm sàng cho dân số khác cohort gốc.

## E2 — retrieval

Vector-only, graph-only, hybrid: cùng 24 queries, corpus, k=5 và allowlisted source URLs. “Vector” là HashingVectorizer 512 chiều dùng ngram/lexical similarity, không phải embedding model ngữ nghĩa được huấn luyện. Graph truy hồi qua topic/entity → supported chunk; hybrid dùng rank fusion của implementation Phase 04.

Recall@5 = số relevant IDs truy hồi / số relevant IDs trong ground truth; MRR@5 dùng vị trí relevant đầu tiên. Chỉ answerable queries vào hai metric này. Citation correctness = exact cached source ID/excerpt/URL đúng / tổng citations, không phải semantic medical entailment. Empty-ground-truth queries được chấm no-evidence accuracy riêng; không tính rỗng là citation đúng giả. Latency đo embedding và Neo4j reads trên máy local, một pass theo strategy, chịu ảnh hưởng cache/warmup; không dùng nó để kết luận causal speed advantage.

## E3 — MAS, trọng tâm hệ thống

12 scenarios × 3 repeats × 2 methods = 72 executions. Thứ tự scenario và thứ tự hai method trong mỗi pair được shuffle với seed 42. Model/policy được load trước timing, corpus được warmup chung.

**Single-workflow baseline** là hàm trực tiếp gọi model, retrieval, policy, render_plan, RuleEngine; không sử dụng Coordinator, AgentRegistry, agent execute hoặc dispatch. Dùng chung frozen model/scaler, Neo4j corpus/hybrid retrieval, serving Q policy với fallback, educational templates và cả hai Safety gates. Nó có cùng quyền truy cập evidence/tools. MAS dùng Coordinator và năm integrated agent thật; Safety chạy hai lần. Cả hai có prediction INSERT thật trong transaction rollback giống nhau. Không dùng baseline thiếu evidence hoặc không có Safety để tạo lợi thế.

- Task completion: đúng expected status, prediction presence, evidence presence, ít nhất một relevant section, rule/error/fallback nếu được yêu cầu. Một BLOCKED an toàn trên câu hỏi lành tính vẫn là task failure.
- Evidence correctness: phần evidence vừa có provenance được admission vừa nằm trong relevant section của ground truth; lấy mean theo evidence-bearing case. Empty cases loại khỏi denominator, hiển thị evidence_cases.
- Citation provenance: exact source metadata/excerpt/URL hợp lệ, báo tách khỏi relevance.
- Safety pass: có đúng input/output gates, không phát hành sau veto, không evidence bị giữ lại lọt ra; required rule có mặt ở scenario tương ứng. Đây là software invariant trên tập nhỏ, không clinical safety certification.
- Latency: thời gian chạy workflow gồm actual prediction INSERT, không gồm mở connection/reflection/rollback/snapshot serialization ở cả hai. Không so sánh full API persistence ở một bên với compute ở bên kia. Báo mean và p95, không cam kết throughput.

JSON ghi thêm paired output mismatches cho status, score, evidence IDs, RL action và response hash. Mục tiêu là kiểm chứng coordination, correlation, control và auditability. Nếu completion/evidence/safety giống nhau thì không tuyên bố MAS tốt hơn. Latency local dao động, không có kiểm định significance hoặc clinical trial.

## E4 — educational RL

Q-learning **serving selector** và rule-based baseline dùng cùng 300 seeds `100000..100299`, cùng simulator/reward/horizon. Không chọn lại seed huấn luyện hoặc policy dựa trên held-out kết quả. Exported serving và evaluator dùng chung selection/fallback; trajectory parity được assert. Báo mean reward, completion, population reward variance, unsafe-action attempts, episode length và fallback count. Curve lấy từ training_history.csv thật của notebook Phase 06, ghi SHA256 của history trong manifest; Phase 07 không huấn luyện lại.

Unsafe attempts nghĩa là action thử dưới restricted simulator context; không tương đương clinical medication attempts. Policy chỉ có sáu action giáo dục. Reward/completion là simulator proxy, không kết quả học tập/sức khỏe thật. Rule baseline có thể tốt hơn Q; giữ nguyên kết quả này.

## E5 — rules và fault handling

41 rule fixtures Phase 05 cộng 12 workflow scenarios và hai fault probes (timeout, conflicting source) = 55 cases. Bao gồm safe queries, medication requests, missing evidence, missing model/Neo4j/policy, prompt injection, diagnosis request, timeout và conflicting/untrusted source. Missing model không tạo score, missing graph không tạo citation, missing policy báo fallback version/source, unsafe input dừng business dispatch.

Conflicting evidence probe thay một câu trong evidence có ID/URL thật: provenance gate phải phát hiện khác snapshot và giữ lại output. Nó không phải benchmark nhận biết hai hướng dẫn y khoa mâu thuẫn nhưng đều có provenance hợp lệ; khả năng đó chưa triển khai trong corpus overview này. Timeout probe có agent async sleep cố ý với budget 1ms; không chứng minh interruption của blocking DB/ML calls.

`pass_rate` E5 đo đúng expected behavior, gồm cả safe-query false positives. Evaluator lưu failure thật, không thay bằng 1.0; exit code failure dành cho rule/invariant/unsafe-release failures. Safe overblocking làm giảm measured score và được báo trong validation report. Runner phân biệt benchmark performance với regression test execution.

## Provenance và chống metric dựng sẵn

Mỗi `{name}.manifest.json` có UTC timestamp, code_version, git_commit nếu có, full source-file SHA256 map, config, dataset/artifact SHA256, seeds và dependency versions. Workspace hiện không phải Git repository: dùng content-addressed `source-sha256:…`, git_commit=null; không tạo Git/commit giả. Manifest không chứa credential/connection URL.

Output hashes bao gồm JSON, summary CSV, rows CSV, PNG. API `/api/v1/experiments` chỉ trả report khi manifest đầy đủ và checksum output khớp; file thiếu/tamper → unavailable, report=null. `/api/v1/experiments/{name}/figure` cùng kiểm tra manifest, enum tên và path containment. UI chỉ tải figure từ endpoint này. Không extrapolate hoặc vẽ placeholder khi thiếu kết quả. Unit/API tests kiểm tra absent/unmanifested/tampered output; browser kiểm tra PNG load thật.

Manifest kiểm tra tính toàn vẹn của artifact local, không phải chữ ký chống một tác nhân sửa cả output lẫn manifest. Kết quả được gắn code/dataset version tại thời điểm chạy; một report cũ không tự trở thành measurement cho source mới. `check_phase07.py` rerun mọi evaluator và kiểm tra frozen model/policy digest trước/sau. Báo cáo kết quả thực tế mới nhất: `docs/validation/phase07/report.md`, `results.json`, các CSV/JSON gốc.

## Tham khảo kỹ thuật

Frontend dùng Vite proxy theo [Vite server options](https://vite.dev/config/server-options); unit runner theo [Vitest guide](https://vitest.dev/guide/); browser lifecycle/config theo [Playwright test configuration](https://playwright.dev/docs/test-configuration). Evidence links trỏ tới [NIDDK overview](https://www.niddk.nih.gov/health-information/diabetes/overview), snapshot/digest và giới hạn nguồn theo Phase 04, không đổi corpus khi chạy evaluation.
