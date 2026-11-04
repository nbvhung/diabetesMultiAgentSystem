# CHƯƠNG 4. CÁC THÀNH PHẦN HỆ THỐNG

## 4.1. Diabetes dataset và chống leakage

Pima có 768 hàng, tám feature số và nhãn Outcome nhị phân; 500 nhãn âm, 268 dương. Bộ dữ liệu lịch sử mô tả nữ giới có nguồn gốc Pima từ 21 tuổi, không đại diện mọi giới/tuổi/dân số. Dữ liệu được tải từ mirror có checksum khóa [7]; giấy phép tái phân phối chưa được xác minh. Raw rows không được hiển thị trong UI hoặc đưa vào database demo.

**Bảng 4.1. Tám feature theo thứ tự phục vụ.** Nguồn: data card, `ml/pipeline.py` và AssessmentInput.

| Feature | Đơn vị / ý nghĩa trong Pima | Xử lý zero |
|---|---|---|
| pregnancies | Số lần mang thai | Zero hợp lệ |
| glucose | Glucose 2 giờ theo dữ liệu, mg/dL | Missing |
| blood_pressure | Huyết áp tâm trương, mmHg | Missing |
| skin_thickness | Độ dày nếp da, mm | Missing |
| insulin | Insulin 2 giờ, µU/mL | Missing |
| bmi | Chỉ số khối cơ thể, kg/m² | Missing |
| diabetes_pedigree | Chỉ số pedigree của dataset | Theo numeric input |
| age | Tuổi, năm | Theo numeric validation |

Split phân tầng seed 42: train 537, validation 115, test 116; test có 41 dương/75 âm. Median imputer và StandardScaler chỉ fit trên train. Validation chọn checkpoint; test chỉ đo cuối. Không SMOTE/tuning threshold trên test. Không có patient IDs để chứng minh độc lập theo người nếu dataset có lặp lượt khám; đây là giới hạn phải nêu, không tự tạo patient split.

## 4.2. Deep Learning training và evaluation

MLP 8→32→16→1 dùng ReLU và dropout 0.15. Loss là BCEWithLogitsLoss; Adam lr 0.001, batch 32, tối đa 200 epochs, patience 20 và min_delta 1e−5. Huấn luyện thật kết thúc epoch 44; checkpoint tốt nhất tại epoch 24. Threshold sigmoid score 0.5 được khóa; score chưa được hiệu chỉnh thành xác suất lâm sàng.

![Hình 4.1. Lịch sử loss MLP](figures/dl_training.png)

Nguồn Hình 4.1: `experiments/results/phase02/learning_history.csv` và PNG cùng lần train. Train loss tiếp tục giảm không có nghĩa validation tiếp tục tốt hơn; checkpoint được chọn bằng validation minimum. Phase 08 không train lại để thay đổi hình hoặc metric.

![Hình 4.2. Diagnostics trên test split của MLP](figures/prediction_diagnostics.png)

Nguồn Hình 4.2: artifact evaluation Phase 02. Confusion matrix, ROC, PR và reliability cần đọc cùng nhau: AUC mô tả khả năng xếp hạng, còn false negatives ở threshold cho thấy rủi ro bỏ sót. MLP bỏ sót 19/41 nhãn dương; không dùng kết quả này để trấn an hoặc chẩn đoán người sử dụng.

Baseline LR(max_iter=2000) và RF(300 trees, min_samples_leaf=2) dùng cùng train preprocessing/split. PR-AUC trong dự án là average precision. Kết quả số tự động trích từ CSV ở Chương 5; LR có accuracy/F1 cao hơn MLP trên split này. Không kết luận DL tốt hơn chỉ vì mô hình sâu hơn.

## 4.3. Prediction Agent

Loader kiểm version, feature order, các SHA256, checkpoint và serving metadata trước inference. PyTorch load dùng weights_only=True; preprocessing joblib chỉ được dùng từ artifact đáng tin. Model chạy eval/inference_mode, không cập nhật weights. Input ngoài training bounds hoặc zero-missing có warning; không clamp để làm output “đẹp”.

Agent giữ vai trò suy luận định lượng và persistence; Education nhận ý nghĩa nghiên cứu cùng limitations, không raw feature profile để gửi Groq. Một assessment synthetic có thể cho score 0.0155 trong run demo cụ thể, nhưng đây là output đo của run đó, không phải score hardcode của giao diện hay một minh chứng bệnh nhân âm tính.

## 4.4. Knowledge Graph và data sources

Corpus có 14 trang NIDDK public về diabetes, được snapshot với URL, thời điểm truy cập, source hash và chunk IDs. Có 449 chunk và 11 assertion hỗ trợ bằng exact clause trong designated section. Entity/topic labels phục vụ routing giáo dục; không có knowledge được “suy ra” từ correlation của bảng Pima.

Một assertion về yếu tố nguy cơ phải có quote hỗ trợ trong trang risk; một quan hệ về biến chứng mắt phải trỏ đúng đoạn tương ứng, không nhận bất kỳ đoạn có từ eye. Seed idempotent thay support edge của assertion đã sinh; release của corpus đi vào retrieval. Quy tắc curation này giúp audit cụ thể nhưng vẫn có phạm vi hẹp, không phải ontology diabetes hoàn chỉnh hoặc tập guideline điều trị.

## 4.5. RAG và Knowledge Agent

Pipeline chuẩn bị corpus → domain/topic routing → graph candidate access → lexical/dense pooling → cross-encoder rerank → evidence adequacy. Encoder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và reranker `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` là pretrained multilingual models chạy CPU; revision/files được kiểm hash. Requests không tự tải models hoặc follow URL LLM chọn.

Tối đa ba passages, tối đa hai cùng nguồn; reranker xét đến 16 query/passage pairs. Similarity/reranker score không phải độ tin cậy y khoa đã hiệu chỉnh. Khi evidence yếu, Coordinator có thể dùng topic rewrite lượt 2; sau giới hạn vẫn không đủ thì hỏi làm rõ. Thiếu graph không được mô tả như retrieval thành công chỉ vì local corpus còn trên disk.

![Hình 4.3. RAG evaluation theo artifacts đã đo](figures/rag_evaluation.png)

Nguồn Hình 4.3: `diabetes_rag` bundle, 40 development + 40 diagnostic + 40 confirmatory phrasings và các câu không trả lời được chấm riêng. Labels dựa nguồn/section do dự án soạn, chưa phải semantic-answer gold standard của chuyên gia. Confirmatory phrasings vẫn cùng topics/corpus, không phải external dataset.

## 4.6. Education Agent và Groq

LLM được gọi qua Groq inference API với model cấu hình `openai/gpt-oss-20b`. Không có quá trình tự train LLM “thành ChatGPT chuyên khoa” trong dự án; 449 passages không tự trở thành bộ fine-tuning đã được chuyên gia gán nhãn. Groq nhận câu hỏi đã redaction và admitted public evidence, không nhận raw assessment hoặc database credentials.

Output yêu cầu JSON schema gồm atomic claims và supports. Adapter giới hạn token/context, timeout, không follow redirect và kiểm model ID/finish_reason/usage. Với GPT-OSS, reasoning để riêng và không đưa vào output công bố. JSON hợp lệ chỉ thỏa cấu trúc; structured-output rejection, timeout hoặc thiếu key vẫn có thể xảy ra [6]. Fallback giữ tiếng Anh nguyên văn nguồn khi cần và ghi extractive, không giả là câu trả lời tiếng Việt do LLM sinh.

## 4.7. Verifier và Safety Agent

Verifier kiểm rằng evidence đúng snapshot/URL/quote, claim có supports và các số được hỗ trợ; proof buộc vào candidate digest. Prose LLM còn cần một review call riêng. Coordinator lặp kiểm tra publication trước Safety output, nên không chỉ tin một trường `verified=true` từ model. Hai role dùng cùng provider vẫn có thể mắc lỗi tương quan; không gọi đó là hai chuyên gia độc lập.

Safety ưu tiên ở cả đầu và cuối. Yêu cầu điều chỉnh insulin bị từ chối trước gọi business agents; nội dung output vượt phạm vi, evidence untrusted hoặc action ngoài whitelist bị giữ lại. Tests có safe queries, medication, missing evidence/model/graph/policy, timeout, injection và quote tampering. Conflicting-evidence probe sửa quote có chủ ý để kiểm provenance; chưa đánh giá hai hướng dẫn thật mâu thuẫn nhưng đều có nguồn hợp lệ.

## 4.8. RL Decision Agent và MDP

State gồm prediction_band, knowledge, engagement, evidence, safety, previous_action và remaining; shape (3,3,3,3,2,7,7), tương ứng 7938 trạng thái. Knowledge/engagement trong serving là simulated defaults, không phải mức hiểu biết thật được đo từ người dùng. Runtime chọn một next action mỗi run, không thực hiện một khóa học nhiều lượt hoặc học online.

**Bảng 4.2. Sáu action giáo dục.** Nguồn: `rl/mdp.py`.

| Action | Vai trò |
|---|---|
| EXPLAIN_PREDICTION_LIMITATIONS | Giải thích giới hạn score nghiên cứu |
| PROVIDE_GENERAL_EDUCATION | Giáo dục chung từ nguồn |
| SHOW_EVIDENCE | Hiển thị dẫn chứng |
| ASK_COMPREHENSION_QUESTION | Đề xuất kiểm tra hiểu |
| REQUEST_CLARIFICATION | Làm rõ chủ đề hoặc nguồn còn thiếu |
| SUGGEST_CLINICIAN_DISCUSSION | Hướng dẫn trao đổi với nhân viên y tế |

Reward gồm −0.2 mỗi step, +1.5 cho knowledge gain, +0.5 cho engagement gain, −4 unsupported, −0.75 lặp action, +0.3 cho evidence-supported general/show, +6 educational completion hoặc +2 restricted handoff; unsafe-context action nhận −20. Các con số do simulator thiết kế; không biểu diễn lợi ích sức khỏe. α=0.15, γ=0.95; epsilon giảm từ 1 theo 0.9994^episode với sàn 0.05.

Huấn luyện ba seeds 11/29/47, 8000 episode/seed, tổng 24000. Chọn policy bằng validation seeds 200000–200099; đánh giá trên 300 seeds 100000–100299. Không chọn policy lại bằng test reward. Serving loader kiểm numeric NPZ/shape/finiteness/hash, mask action và unvisited fallback. Missing/corrupt policy báo decision_source=fallback cùng version riêng; trace phân biệt proposed_action/effective_action và override reason.

![Hình 4.4. Reward curves từ lịch sử training](figures/rl_rewards.png)

Nguồn Hình 4.4: `experiments/figures/phase06/reward_curves.png`, sinh từ notebook RL đã thực thi; không train lại Phase 08. Đường tăng reward trong simulator không chứng minh người dùng thật học tốt hơn hoặc policy vượt rule baseline trên held-out seeds.

## 4.9. Cơ chế phối hợp trong một run thực

Run HTTPS assessment có Prediction, Knowledge, RL, Education, Verifier và Safety thực thi; Safety có hai gate. Coordinator ghi lý do dispatch và phương thức công bố. Agent timeout/fallback không bị che; frontend chỉ vẽ trace sau khi response về. Run ID và events của lần thực hiện nằm trong `docs/validation/phase08/public_demo.json` để có thể đối chiếu thay vì dựng timeline đẹp trong báo cáo.

![Hình 4.5. Trace thực tế qua HTTPS](figures/actual_trace.png)

Nguồn Hình 4.5: JSON run thực đã commit và được GET readback. Thứ tự event là dữ liệu thực; đây là rendering trace, không phải mô phỏng tiến độ agent. Trạng thái DEGRADED trong run có research warning không làm mất tính thật của model/LLM/evidence.
