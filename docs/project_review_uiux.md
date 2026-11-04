# Rà soát dự án: UI/UX, huấn luyện và việc cần làm tiếp

## Kết luận

Hệ thống đã có DL được huấn luyện, KG/RAG có nguồn, LLM qua Groq và workflow sáu agent chạy thật. Nó đáp ứng một demo nghiên cứu có giải thích được quá trình phối hợp. **Chưa có đủ bằng chứng để coi mô hình dự đoán, policy RL hoặc câu trả lời LLM là hệ thống hỗ trợ lâm sàng đáng tin cậy.** UI đẹp hơn không làm thay đổi chất lượng huấn luyện.

Đợt này nâng cấp frontend và đọc lại artifact thí nghiệm đã đo; không huấn luyện lại, thay checkpoint, đổi ngưỡng hoặc sửa kết quả. Các số dưới đây có thể kiểm tra trong CSV/JSON gốc. [Kiểm chứng giao diện mới](validation/uiux/report.md).

## 1. UI/UX đã thay đổi

- Chuyển giao diện chính sang tiếng Việt; phân biệt rõ hỏi kiến thức, khảo sát mô phỏng, hành trình agent và thí nghiệm.
- Dashboard có điểm bắt đầu rõ ràng, chủ đề gợi ý, sơ đồ Coordinator/sáu agent, thư viện nguồn và trạng thái backend thực tế. Không thêm hồ sơ người dùng, số bệnh nhân hoặc chỉ số sức khỏe giả.
- Composer có gợi ý, giới hạn ký tự, gửi bằng Ctrl/Cmd+Enter, trạng thái chờ theo thời gian thực đã trôi qua và chống gửi trùng. Chưa có streaming nên không diễn hoạt các agent như thể đã biết tiến độ backend.
- Đọc câu trả lời theo từng claim với citation đánh số; trích đoạn và metadata nguồn mở khi cần. Fallback nguyên văn nguồn, thiếu evidence và Safety veto có trạng thái riêng.
- Điểm MLP là số nghiên cứu và nhãn dự đoán, không gắn nhãn “bạn có nguy cơ thấp/cao” hay biến score thành xác suất y khoa.
- Trace kỹ thuật chuyển sang trang riêng; thêm bộ lọc quyết định, metadata được lọc, hành động RL đề xuất/thực tế và hai Safety gate. Sửa lỗi UI khi `duration_ms` trong trace là `null`.
- Thí nghiệm có nhóm lọc và tóm tắt chỉ số lấy từ API/artifact đã xác minh; thiếu artifact hiển thị chưa có kết quả.
- Điều hướng mobile, trạng thái mở/đóng menu, nhãn input, bàn phím, skip link, tăng cỡ chữ/độ tương phản và hỗ trợ `prefers-reduced-motion`. Đây chưa phải chứng nhận đạt toàn bộ WCAG.

## 2. DL: đã train thật, nhưng hiệu quả chưa vượt baseline rõ ràng

Nguồn: [model card](model_card.md), [CSV prediction](../experiments/results/prediction.csv), [learning history](../experiments/results/phase02/learning_history.csv).

MLP PyTorch 8→32→16→1, dropout 0,15, early stopping. Pima có 768 mẫu, chia train/validation/test 537/115/116; test có 41 nhãn dương và 75 nhãn âm. Imputer/scaler fit trên train. Chạy 44 epoch, chọn checkpoint epoch 24 theo validation BCE.

| Mô hình | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC/AP |
|---|---:|---:|---:|---:|---:|---:|
| MLP | 0,758621 | 0,709677 | 0,536585 | 0,611111 | 0,863415 | 0,781957 |
| Logistic Regression | 0,775862 | 0,777778 | 0,512195 | 0,617647 | 0,862439 | 0,783225 |
| Random Forest | 0,732759 | 0,666667 | 0,487805 | 0,563380 | 0,827967 | 0,757576 |

MLP có khả năng xếp hạng trên split này, nhưng LR có accuracy/F1 tốt hơn một chút. Chênh lệch accuracy MLP/LR chỉ tương ứng 2 mẫu đúng trên 116 mẫu; chưa có kiểm định/độ bất định để khẳng định khác biệt đáng kể. MLP bỏ sót 19/41 nhãn dương ở ngưỡng 0,5; đây là hạn chế quan trọng nếu chỉ nhìn accuracy.

Tại epoch 24: train loss 0,433432, validation loss 0,502334. Tại epoch 44: train loss giảm còn 0,408441, validation loss tăng lên 0,521356. Điều này phù hợp với nguy cơ overfit sau checkpoint được chọn; early stopping đã giữ checkpoint tốt hơn theo validation, không chứng minh đã giải quyết toàn bộ overfit.

Pima là cohort lịch sử hẹp; không suy rộng sang mọi giới, tuổi, dân số hay tình huống lâm sàng. Score chưa được calibration; Brier MLP 0,151729 và LR 0,149270 là đánh giá trên split nhỏ, không phải bảo đảm xác suất cá nhân.

**Cần làm tiếp:** đăng ký protocol CV trước, fit preprocessing trong từng fold, chọn hyperparameter trên train/validation; báo mean/std hoặc khoảng tin cậy phù hợp. Giữ baseline LR, RF và cùng ngân sách tuning. Chọn threshold/calibration chỉ bằng dữ liệu validation hoặc out-of-fold, không tối ưu theo test đã xem. Tìm tập đánh giá ngoài hoặc phiên bản dữ liệu độc lập trước khi kết luận tổng quát. [Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) và [calibration](https://scikit-learn.org/stable/modules/calibration.html) của scikit-learn giải thích việc tách dữ liệu và ý nghĩa của xác suất đã hiệu chỉnh.

Không tự chuyển model serving sang LR hoặc retrain nhiều lần để lấy điểm test đẹp hơn; thay model cần một thí nghiệm mới có version và bằng chứng.

## 3. RL: train thành công về kỹ thuật, chưa chứng minh lợi ích hơn rule-based

Nguồn: [RL CSV](../experiments/results/rl.csv), [serving policy evaluation](../experiments/results/phase06/exported_policy_evaluation.json).

Training history ghi 24.000 episode: 8.000 cho mỗi seed 11, 29, 47. Policy serving chọn seed 11. Đánh giá simulator dùng 300 seed giữ lại 100000–100299.

| Policy | Average reward | Completion | Variance qua scenario | Unsafe attempts |
|---|---:|---:|---:|---:|
| Q-learning | 4,276 | 0,970000 | 8,358457 | 0 |
| Rule-based | 4,311 | 0,983333 | 8,504162 | 0 |

Q-learning thấp hơn rule-based về reward và completion trong phép đo này. Zero unsafe attempts ở cả hai chỉ mô tả simulator; không phải kết quả an toàn y khoa. Reward là hàm do dự án xây dựng, chưa đo lợi ích học tập trên người thật.

Ngoài ra, renderer có thể override hành động RL để ưu tiên chế độ trả lời đã kiểm chứng. Ví dụ smoke run đã lưu đề xuất `SHOW_EVIDENCE`, thực tế `PROVIDE_GENERAL_EDUCATION`, với mã override rõ ràng. Vì vậy “agent RL đã chọn một action” chưa chứng minh action đó tạo khác biệt cho người học.

**Cần làm tiếp:** thống kê tỷ lệ action được thực thi/override; phân tích state/action chưa được thăm, lỗi policy và reward shaping; so sánh nhiều seed với baseline cùng simulator và cùng evaluator-serving policy. Kiểm chứng simulator có đủ quyết định không tầm thường trước khi tăng episode. Nếu chưa vượt baseline, giữ kết luận âm và dùng fallback phù hợp.

## 4. KG/RAG: nguồn đã chặt hơn, độ liên quan còn cần cải thiện

Corpus gồm 14 nguồn NIDDK, 449 đoạn, 11 assertion ràng buộc câu hỗ trợ. Encoder/reranker là model upstream pretrained dùng lại; không phải model diabetes mới do dự án huấn luyện.

Nguồn: [RAG CSV](../experiments/results/diabetes_rag.csv). Trên 40 cách hỏi confirmatory, cùng corpus, tối đa 3 đoạn:

| Phương pháp | Recall@3 | Precision trên đoạn trả về | MRR@3 | Provenance |
|---|---:|---:|---:|---:|
| Semantic | 0,313819 | 0,362500 | 0,575000 | 1,0 |
| Graph | 0,293472 | 0,391667 | 0,508333 | 1,0 |
| Hybrid + reranker | 0,290972 | 0,570833 | 0,625000 | 1,0 |

Hybrid cao hơn về precision/MRR, thấp hơn semantic về recall và tốn thêm thời gian. Recall mẫu số là tất cả chunk có nhãn nguồn/mục, có thể lớn hơn k=3; nhãn này thô và có thể coi đoạn hợp lệ ở mục khác là sai. Không diễn giải provenance 1,0 thành “câu trả lời đúng 100%”. Các cách hỏi đã được xem trong thí nghiệm và có chung topic/nguồn với development; chúng không phải kiểm định lâm sàng ngoài dự án.

**Cần làm tiếp:** xây tập mới có expected facts và điều kiện từ chối rõ ràng; đánh giá song ngữ, relevance/faithfulness/citation support, không chỉ đúng URL. Rà soát chunk bị thiếu ngữ cảnh và gán topic theo đoạn thay vì chỉ theo trang. So sánh ablation của graph constraints, dense retrieval và reranker với cùng corpus; chỉ điều chỉnh sau khi phân tích lỗi development, rồi chạy tập mới đã khóa.

## 5. LLM: đang dùng API, chưa có LLM do dự án tự train

Groq chạy model `openai/gpt-oss-20b` đã pretrained. Cấu hình JSON, prompt ràng buộc evidence và Verifier là tích hợp hệ thống; không phải fine-tuning. Hai smoke execution trước đây và một lượt UI→API thật trong đợt này xác nhận kết nối/contract/flow hoạt động. Chúng không ước lượng độ chính xác trả lời.

449 đoạn NIDDK phục vụ truy hồi; chúng không tự trở thành một bộ supervised fine-tuning gồm câu hỏi/câu trả lời/expected refusal được chuyên gia kiểm chứng. Chưa có lý do thí nghiệm để tự train một LLM lớn trên máy hiện tại.

**Cần làm tiếp trước fine-tuning:** benchmark LLM thực sự với câu hỏi cố định và rubric; đánh giá từng claim có được đoạn dẫn chứng hỗ trợ, có giữ đúng loại bệnh/phạm vi/dân số và có trả lời câu hỏi không. Thêm chuyên gia/người đánh giá độc lập, kiểm tra tiếng Việt, prompt injection, yêu cầu điều chỉnh thuốc, thiếu nguồn và hai nguồn thật mâu thuẫn. Verifier dùng cùng provider có thể mắc lỗi tương quan; tỷ lệ nó chấp nhận không phải medical accuracy.

## 6. MAS: tích hợp thật, nhưng phép so sánh chưa tách riêng hiệu ứng phân rã agent

Nguồn: [MAS CSV](../experiments/results/diabetes_mas.csv), [protocol](diabetes_expansion_experiments.md).

| Phương pháp | Completion | Evidence relevance có điều kiện | Latency trung bình |
|---|---:|---:|---:|
| Workflow đơn | 0,727273 | 0,750000 | 435,45 ms |
| Multi-agent | 0,863636 | 0,650000 | 593,69 ms |

Đây là 22 scenario lặp hai lần mỗi phương pháp, không phải 44 câu hỏi độc lập. Provider tắt ở cả hai nên số câu trả lời LLM sinh là 0. MAS có tối đa hai lượt truy hồi và repair, baseline có một lượt; do đó tăng completion có thể đến từ ngân sách công cụ/control bổ sung. Evidence relevance lấy trung bình có điều kiện trên các run công bố evidence; mẫu số hai phương pháp khác nhau. Không kết luận MAS thông minh hơn nói chung từ bảng này.

**Ưu tiên nghiên cứu cao nhất:** so sánh matched-budget với cùng model, evidence, tools, số lần gọi và token budget; paired scenarios/seeds. Ablation bỏ feedback, bỏ Verifier, bỏ graph để đo đóng góp từng phần. Đo cả completion, support của claim, safety pass, latency và chi phí; báo cả trường hợp MAS kém baseline. Giữ trace để chứng minh vì sao mỗi agent được gọi, không dùng số lượng agent thay cho hiệu quả.

## 7. Thứ tự công việc đề xuất

| Ưu tiên | Việc | Điều kiện hoàn thành |
|---|---|---|
| P0 | Khóa benchmark diabetes mới + rubric expected facts/refusal | Dataset version, nguồn, nhãn, train/dev/eval tách rõ; có review độc lập |
| P0 | Đánh giá LLM và MAS matched-budget thật | CSV/JSON/manifest có usage/latency; claim-level review; không claim ưu thế khi chưa được chứng minh |
| P1 | Phân tích lỗi RAG | Câu hỏi thất bại/đoạn không liên quan được phân loại; cải tiến được kiểm tra trên tập khóa mới |
| P1 | Kiểm chứng lại DL bằng CV/calibration có kiểm soát | Preprocessing trong fold, baseline công bằng, không leakage hoặc tuning test |
| P1 | Rà soát simulator/RL và tỷ lệ override | Reward có lập luận, baseline/multi-seed cùng ngân sách; báo kết quả âm nếu có |
| P2 | UX nghiên cứu với người dùng thử bằng kịch bản synthetic | Đo hoàn thành tác vụ, khả năng hiểu citation/cảnh báo; không suy luận thành hiệu quả sức khỏe |
| Sau phạm vi hiện tại | Auth, rate limiting, triển khai, memory/streaming nếu cần | Thiết kế và yêu cầu riêng cho Phase 08; chưa tự triển khai |

Các mục trên là kế hoạch sau rà soát, chưa được báo là đã thực hiện. Trọng tâm tiếp theo nên là **chất lượng trả lời có nguồn và đóng góp đo được của MAS**, không chỉ tăng epoch hoặc đổi sang model lớn hơn.
