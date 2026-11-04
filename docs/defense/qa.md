# Câu hỏi phản biện kỹ thuật

## 1. Vì sao gọi là Multi-Agent, không chỉ pipeline?

Mỗi agent có task/result contract, quyền tool, timeout, mục tiêu và phản ứng riêng; Coordinator xử lý trạng thái/feedback, Verifier reject và Safety veto. Bằng chứng ở definitions/tests và actual trace. Tuy vậy đây là centralized MAS với autonomy giới hạn; agent decomposition không tự chứng minh tốt hơn workflow trực tiếp.

## 2. Các agent có cần là các LLM khác nhau không?

Không. Prediction là learned classifier, Knowledge là retrieval, RL là policy, Safety là rules. Education và Verifier gọi cùng provider bằng role/call khác nhau. Không có sáu foundation models hoặc sáu process riêng.

## 3. Coordinator làm gì?

Tạo run state, chọn agent theo input, dispatch typed task, kiểm Result, quản lý deadlines/budgets, retry/repair, lặp publication admission, gọi hai Safety gates và trả snapshot để transaction commit. Nó không dùng prompt để cấp thêm tool permissions.

## 4. Điều gì chứng minh agent phối hợp thật?

POST thật tạo correlated messages/events, có actual model/evidence/action/verification/safety output; GET đọc lại cùng run/trace từ SQL. Evidence yếu dẫn tới retry; unsafe insulin khiến business agents SKIPPED. UI không tạo các kết quả này.

## 5. Tại sao cần DL trong khi LR tốt hơn?

DL đáp ứng thành phần phân loại có huấn luyện của đề tài và cho một serving tool để nghiên cứu phối hợp. Trên split này LR có accuracy/F1 cao hơn; không có lý do khoa học ép MLP phải thắng. Kiến trúc agent tách model nên có thể so/đổi model bằng nghiên cứu versioned sau này, không đổi lén trong demo.

## 6. Model đã train chưa? LLM đã train chưa?

MLP và Q-policy đã train bằng notebook thực. Encoder/reranker dùng pretrained weights. LLM dùng Groq inference API, không tự train/fine-tune. Không gọi việc viết prompt hoặc nạp corpus là training LLM.

## 7. Dữ liệu Pima có phải synthetic không?

Không, đó là nghiên cứu lịch sử 768 hàng. Chỉ input form demo được dự án soạn synthetic; database case có ràng buộc synthetic=true. Không đưa raw Pima row lên UI làm bệnh nhân demo.

## 8. Vì sao Pima không dùng chẩn đoán người Việt?

Population hạn chế, endpoint lịch sử và single split không xác nhận ngoại suy. Score chưa calibrated và thiếu external clinical validation. MLP còn FN 19/41 positive labels trên test ở threshold 0.5.

## 9. Chống data leakage thế nào?

Split stratified seed 42 trước fit preprocessing, median/scaler chỉ fit train, validation chọn epoch, test đo cuối. Không SMOTE/tune threshold trên test. Thiếu patient identifiers nên không khẳng định person-level independence.

## 10. Vì sao epoch 24 nhưng lịch sử có 44 epochs?

Epoch 24 cho validation loss nhỏ nhất; patience 20 dẫn tới dừng ở 44. Serving load checkpoint tốt nhất, không dùng last epoch hoặc chọn bằng test.

## 11. PR-AUC được tính ra sao?

Dự án dùng average_precision_score; không phải trapezoidal area của PR curve. Cần ghi định nghĩa khi so kết quả. Accuracy, recall, F1 và ROC-AUC có ý nghĩa khác nhau.

## 12. Graph có gì ngoài các vector?

Source/evidence/topic/concept/assertion nodes và các relation có supporting quote; 11 assertions curated trong corpus hiện hành. Nó không suy ra causal relations từ Pima. Query được giới hạn, không cho LLM chạy Cypher tùy ý.

## 13. Neo4j có thật sự được dùng trong retrieval không?

Có, candidate reads gắn corpus release. Graph unavailable làm Knowledge UNAVAILABLE và không trả citation, được kiểm bằng fault API. Local embeddings không được giả làm graph access thành công.

## 14. URL đúng có đủ chứng minh câu trả lời đúng không?

Không. Cần đúng source/quote, relevance với câu hỏi và claim entailment. Provenance 1.0 là integrity, không phải medical accuracy. Verifier cũng fallible, nhất là khi author/reviewer cùng provider.

## 15. RAG có hoàn toàn ngăn hallucination không?

Không. Retrieval có thể sai, nguồn hẹp, LLM có thể suy diễn vượt quote. Hệ thống thêm deterministic admission, separate review và Safety/fallback; chưa có chứng nhận hoặc expert clinical benchmark.

## 16. Tại sao không train LLM riêng từ 449 chunks?

Đó là corpus tham khảo, không phải bộ SFT đủ nhãn chất lượng/expected refusal. Train lớn tốn tài nguyên và không tự bảo đảm bám nguồn. Hiện dùng pretrained API với retrieval và evaluation rõ sẽ phù hợp phạm vi hơn.

## 17. RL học điều gì?

Ưu tiên next educational action trong simulator hữu hạn theo reward proxy: kiến thức/engagement/evidence và ngân sách. Không học liều insulin hoặc tối ưu outcome sức khỏe. Runtime chọn một action/run, không học online.

## 18. State/action/reward cụ thể?

State có 7 biến, 7938 states; sáu action giáo dục. Reward: −0.2 step, gains kiến thức/engagement, penalty unsupported/repeat, completion bonus và −20 unsafe-context action. Các thông số là thiết kế simulator; xem rl_mdp và source reward.

## 19. Vì sao runtime knowledge/engagement lại giả lập?

Chưa có phép đo người dùng thật hoặc dữ liệu tương tác. Vì vậy context được gắn SIMULATED_DEFAULTS_NOT_MEASURED. Không suy ra “người này ít hiểu” từ tuổi/giới/score; không nhận hiệu quả giáo dục cá nhân hóa đã được chứng minh.

## 20. Q-learning có vượt rules không?

Chưa. Saved serving reward Q 4.276 vs rules 4.311; completion 0.97 vs 0.983333 trên cùng 300 held-out seeds. Báo kết quả âm thay vì đổi reward/baseline sau khi xem test.

## 21. Rule-based khác RL và ưu tiên ra sao?

Rules trực tiếp mã hóa constraints; Q cập nhật từ transitions/rewards. Action masks và Safety là ràng buộc bắt buộc, có thể veto mọi learned recommendation. Q-value không cấp quyền điều trị.

## 22. Khi Groq lỗi, có bịa lời đáp hay citation không?

Không. Nếu còn admitted evidence thì exact-source fallback có nhãn extractive; không có thì clarification/withheld. Missing auth/rate/schema/timeout có code sanitize. Mode hiển thị đúng, không gọi fallback là LLM generation.

## 23. LLM benchmark 100% nghĩa gì?

Không có 100% clinical accuracy. Sáu câu: ba LLM outputs và cả ba được automated verifier chấp nhận; hai clarification và một extractive fallback. Coverage 3/6, acceptance conditional 3/3. Mẫu nhỏ, reviewer cùng provider và không có medical expert review.

## 24. MAS có tốt hơn baseline không?

Saved offline completion cao hơn nhưng có retry/repair budget cao hơn; evidence relevance có điều kiện lại thấp hơn và latency cao hơn. Không tách được hiệu ứng decomposition. Cần matched-budget/ablation và human grounding evaluation trước superiority claim.

## 25. Timeout có kill được mọi computation không?

Không. asyncio task budget xử lý async timeout nhưng native/thread blocking có thể tiếp tục. Warmup tách trước budget; graph/HTTP có timeout riêng. Không nhận hard realtime guarantee.

## 26. Tại sao HTTP 201 sau commit?

Để phản hồi “đã tạo run” chỉ xảy ra khi prediction/snapshot/events được lưu. DB failure rollback và 503 sanitized. GET readback qua new request xác nhận durable storage; in-memory status không đủ.

## 27. Làm sao không lẫn concurrent workflows?

Run-local state/registry/messages/budget, UUID correlation và unique event sequence theo run. Shared models/policy readonly với khóa; tests concurrent creation/readback kiểm tra correlation. Chưa benchmark tải production.

## 28. Có deploy cloud chưa?

Chưa. URL thật là Quick Tunnel HTTPS đến máy cá nhân, có gateway password; cloud hosting NOT_COMPLETED. Chỉ link frontend không chứng minh full backend/DB đã chạy trên cloud.

## 29. Docker đã chạy thành công chưa?

Chưa trên máy này. Compose config parse được nhưng engine không có; `up` lỗi docker_engine pipe. Cần host Docker chạy build/start/health/workflows/restart/volume persistence rồi mới đóng acceptance.

## 30. Nếu thầy yêu cầu xác nhận hoàn thành 100%?

Trình audit và tiêu chí cụ thể: các khối nghiệp vụ có code/demo, report có số liệu, nhưng gate Docker còn thiếu và nghiên cứu chưa clinical validated. Không ký 100% khi tiêu chí runtime chưa kiểm chứng; trạng thái Phase 08 hiện BLOCKED, demo native/HTTPS vẫn dùng được.

## 31. Điều gì cần cải thiện đầu tiên?

Đóng Docker runtime gate, đo LLM bilingual coverage/grounding có reviewer độc lập, MAS matched-budget; sau đó CV/calibration DL và simulator realism. Không tăng số agent/epoch để thay cho bằng chứng.

## 32. Quyền dữ liệu và reproducibility xử lý ra sao?

Pima mirror được pin hash nhưng license redistribution chưa xác minh; raw/fitted artifacts ignored. NIDDK snapshots giới hạn public educational text có provenance. Người tái lập dùng trusted bundle hoặc chạy prepare/train, ghi versions/hashes; không giả có remote repo hoặc checkpoints trong Git.
