# CHƯƠNG 5. CODE, DEMO VÀ ĐÁNH GIÁ

## 5.1. Cấu trúc source và tái lập

`backend/app/research` chứa runtime 3.0 hiện hành; `mas` và các schema cũ giữ tương thích; `ml`, `rl`, `knowledge`, `db` chứa tools/persistence. `frontend/src` chứa năm màn hình; `notebooks` giữ EDA/split, DL train, model evaluation và Q-learning. `scripts` tách chuẩn bị dữ liệu, seed, demo, evaluation và deployment. `experiments/results` là CSV/JSON/manifest; `experiments/figures` là đồ thị đã đo. `infra/docker` và Compose root là đóng gói; `docs/report`, `docs/defense` là tài liệu bảo vệ.

Source inventory lưu SHA256 và symbols của các file ở `docs/report/source_inventory.json`. Workspace chưa có Git repository/remote nên code provenance dùng content-addressed source hashes, không bịa commit SHA hoặc clone URL. Checkpoint, raw Pima, `.env`, cached models được ignore; người nhận source cần trusted artifact bundle hoặc tự chuẩn bị/train theo `docs/installation.md`. Một repository có code không đồng nghĩa tự chứa gần 1 GB retrieval weights.

## 5.2. Cài đặt và các chức năng

Môi trường native dùng Python 3.11/CPU và Node/Vite; PostgreSQL tạo schema bằng Alembic head; Neo4j seed nguồn đúng release. Có thể dùng checkpoint đã lưu mà không train lại; nếu thiếu thì chạy bốn notebook trên bản sao nghiên cứu để không thay frozen artifacts. Model/graph loaders kiểm tra manifest trước serving. Groq key chỉ cấu hình env; không phải build-time variable của React.

Năm màn hình là Tổng quan, Hỏi về tiểu đường, Khảo sát mô phỏng, Hành trình agent và Kết quả nghiên cứu. Dashboard đọc readiness; form validate tám feature và yêu cầu xác nhận synthetic; assistant gửi Coordinator; citations mở nguồn thật; monitor tải snapshot/event; experiment cards chỉ đọc bundle có checksum đúng. Giao diện dùng font Be Vietnam Pro và palette tham khảo Nutriwise theo yêu cầu người dùng; không sao chép chỉ số sức khỏe giả từ dashboard tham khảo.

![Hình 5.1. Trang tổng quan trên URL HTTPS tạm](figures/public-overview.png)

Nguồn Hình 5.1: screenshot Chromium thật ở Phase 08; các readiness trạng thái tại thời điểm capture là probes, không phải kết quả lâm sàng. Không dùng mockup do AI tạo.

![Hình 5.2. Câu trả lời của run thực được đọc lại](figures/public-answer.png)

Nguồn Hình 5.2: gateway HTTPS đọc workflow đã commit từ PostgreSQL. Số citation được lấy từ response. Hình thể hiện khả năng truy nguyên; một ảnh không đủ chứng minh chất lượng mọi câu trả lời.

## 5.3. Demo scenarios và phối hợp agent

Scenario 1 dùng synthetic assessment và hỏi yếu tố nguy cơ: model output, một citation và LLM answer được kiểm chứng, 20 events trong trace. Scenario 2 hỏi tăng liều insulin: input Safety veto, business agents không được gọi và không phát hành evidence. Scenario 3 `Tell me about sugar`: evidence chưa phù hợp nên clarification, không có citation thay thế. Ba scenario này chạy HTTP qua URL HTTPS thật và GET readback bằng đúng run ID.

Scenario lỗi graph được kiểm tra riêng trong browser/API regression bằng fault service cố ý; response DEGRADED và không citation. Không tắt graph chính giữa buổi trình bày rồi hứa sẽ khôi phục bằng tay. Có thể xem một fault run được gắn nhãn injection để giải thích kiến trúc. Khi dùng run đã lưu, ghi rõ replay/readback, không giả làm lời gọi mới khi mạng không hoạt động.

![Hình 5.3. Monitor của run thật](figures/public-monitor.png)

Nguồn Hình 5.3: Chromium qua HTTPS, đọc lại persisted run. Monitor chứa RL action, Safety decisions và trace được lọc metadata. Raw rejected drafts hoặc credentials không xuất hiện.

## 5.4. Thiết kế thực nghiệm

E1 so MLP/LR/RF cùng train/test split; E2 so các strategy cùng query/corpus; E3 so MAS/direct workflow cùng tools và điều kiện provider disabled nhưng khác retry budgets; E4 so Q-serving/rules cùng 300 simulator seeds; E5 kiểm finite safety scenarios và lỗi được tiêm có ghi nhãn. Phase 08 bổ sung benchmark Groq 6 câu, ghi rõ trường hợp không sinh LLM. Scenario do dự án soạn không phải dữ liệu bệnh nhân thật hoặc benchmark chuyên gia y tế độc lập.

Mỗi measured bundle có timestamp, code version/source hashes, config, dataset version/hashes, seed, dependency versions và output hashes. Frontend/API từ chối artifact thiếu/tamper. Manifest bảo vệ tính toàn vẹn local, không phải chữ ký chống một người sửa cả metric và manifest. Metric của các lần chạy/corpus khác nhau không được ghép thành so sánh before/after nếu protocol thay đổi.

## 5.5. Kết quả định lượng

Các bảng số đầy đủ được tạo tự động từ CSV trong mục “Bảng kết quả thực nghiệm” kèm báo cáo này. Các nhận xét dưới đây dùng chính artifacts đó, không tự tạo kết quả mới.

E1: MLP accuracy 0.758621, recall 0.536585, F1 0.611111; LR accuracy 0.775862 và F1 0.617647. MLP ROC-AUC 0.863415 gần LR 0.862439. Với 116 mẫu test và một split, chênh nhỏ không đủ kết luận superiority. False negatives 19/41 nhãn dương cho thấy giới hạn đáng kể ở threshold 0.5.

![Hình 5.4. So sánh mô hình trên test split](figures/prediction_evaluation.png)

Nguồn Hình 5.4: `prediction` measured bundle. Ba mô hình dùng cùng dữ liệu và preprocessing, nên có thể mô tả so sánh trên split này; chưa có CV hoặc external validation để khái quát rộng.

E2 confirmatory: hybrid MRR@3 0.625 và precision trong passages trả về 0.570833; semantic recall 0.313819 cao hơn hybrid 0.290972. Provenance 1.0 chỉ nói metadata/quote phù hợp snapshot, không phải mọi passage trả lời đúng câu hỏi. Hybrid chậm hơn vì reranking thực; không dùng tên “hybrid” để khẳng định luôn tốt hơn.

E3 offline: completion MAS 0.863636 so với direct 0.727273, mỗi method 44 executions từ 22 cases lặp hai lần. Conditional evidence relevance tương ứng 0.65/0.75, latency khoảng 593.69/435.45 ms. Hai bên dùng cùng tools nhưng MAS có retry/repair budget cao hơn. Không thể quy toàn bộ chênh lệch completion cho phân rã agent; cũng không được bỏ qua evidence relevance thấp hơn. Số LLM-generated runs của phép đo này bằng 0 vì provider disabled.

![Hình 5.5. Đánh giá hai workflow hiện hữu](figures/mas_evaluation.png)

Nguồn Hình 5.5: `diabetes_mas` bundle. Đây là so sánh hai cấu hình đã mô tả, không phải proof “MAS thông minh hơn”. Cần matched-budget ablation trước kết luận nhân quả.

E4: serving Q average reward 4.276, completion 0.97; rules 4.311/0.983333; reward variance lần lượt 8.358457/8.504162 trên scenarios; cả hai có zero unsafe-context attempts trong finite simulator evaluation. Q không vượt rules ở reward/completion. Action mask và fallback là phần của serving policy được đánh giá, không loại ra để làm số đẹp hơn.

![Hình 5.6. RL serving so với rule baseline](figures/rl_evaluation.png)

Nguồn Hình 5.6: `rl` bundle và cùng held-out seeds. Reward là proxy simulator; completion không phải tỷ lệ người bệnh hiểu hoặc cải thiện sức khỏe.

E5 current regression có 14 expected behaviors đạt trong các nhóm rules, actual workflow và Coordinator fault injection. Bộ lịch sử có scenario false positive riêng không bị sửa nhãn thành PASS. 14/14 chỉ là finite software expectations; không phải 100% an toàn y tế. Chưa có đánh giá đầy đủ conflicting genuine clinical sources hoặc mọi adversarial phrasings.

![Hình 5.7. Tóm tắt finite safety expectations](figures/safety_summary.png)

Nguồn Hình 5.7: `diabetes_safety` CSV/JSON/manifest. Hai fault cases có injection rõ ràng; không nhận là lỗi provider thật vừa xảy ra.

Benchmark Groq Phase 08: 6 fixed questions, 3 genuine LLM outputs, cả 3 được automated verifier chấp nhận. Hai Vietnamese phrasings clarification trước generation; một risk phrasing fallback sau structured-output rejection. Do đó coverage generated-and-accepted là 3/6, còn acceptance có điều kiện trên generated outputs là 3/3. Mean 2278.704 ms trong summary chỉ tính generated cases. Không đổi con số có điều kiện 1.0 thành clinical accuracy hoặc che các non-generation cases.

![Hình 5.8. LLM evaluation có điều kiện](figures/llm_evaluation.png)

Nguồn Hình 5.8: `diabetes_llm` bundle mới. Cần đọc cùng per-question rows và mẫu số sáu câu; hình summary không thể tự thể hiện toàn bộ thất bại/non-generation. Ba outputs được chấp nhận đều ở các English phrasings trong sample này, nên chất lượng tiếng Việt vẫn cần cải thiện và đo rộng hơn.

## 5.6. Final software verification

Phase 08 chạy 249 backend tests không skip; 22 frontend unit tests, TypeScript/Vite build và 6 browser/API scenarios đều PASS. Migration, graph initialization, model/policy/encoder/reranker loads được xác minh trên service test riêng. Các browser cases gồm assessment/persistence, citations, Safety veto, graph down, measured figures, mobile, weak evidence. Bốn gateway tests kiểm authentication, route boundary, request limits và fail-closed configuration; fake transport chỉ dùng cho unit tests của proxy, không thay actual API integration.

Kiểm thử đầu có lỗi do test runner tắt cấu hình LLM làm mock-transport tests đi sai nhánh và chưa migrate workflow database trước khi chạy theo thứ tự; runner được sửa, expected behaviors không đổi. Neo4j test launcher cũng cần thư mục ASCII trong temporary directory trên Windows. Log cuối và các lỗi setup được ghi trong verification report; không nhận các failure hạ tầng test đó là kết quả nghiên cứu y khoa.

## 5.7. Deployment acceptance

URL HTTPS tạm đã được kiểm tra cùng authentication, React build, API và ba workflows thật; browser screenshots không có page errors ở lượt capture. Chỉ gateway được đưa qua tunnel, DB vẫn local. Cloud deployment độc lập là NOT_COMPLETED vì chưa có tài khoản/host. URL tunnel phụ thuộc máy bật và có thể đổi khi restart.

Compose configuration parse PASS nhưng `up --build --wait` fail do không có Docker engine/WSL. Image build, Linux wheels, actual container health/start/restart và persistent volume survival chưa được xác minh. Vì acceptance của Phase 08 yêu cầu Compose chạy được, **final readiness là BLOCKED**, dù bản demo native/HTTPS đã chạy. Cần chạy Compose trên host có Docker, thực hiện workflows và lưu logs/image digests mới có thể đổi thành READY_FOR_DEFENSE.

## 5.8. Hạn chế và hướng phát triển

Ưu tiên nghiên cứu là nhãn answer-level bằng chuyên gia/người đánh giá độc lập, bilingual error analysis, MAS matched-budget/ablations và báo cả chi phí provider. Với DL, cần validation ngoài cohort, cross-validation đúng preprocessing, calibration có tập riêng và phân tích sai số. Với RL, cần simulator realism/override analysis và đo outcome giáo dục thực trước mọi lời khẳng định lợi ích người dùng. Đây là công việc tương lai, không được ghi là đã hoàn thành.

Ưu tiên kỹ thuật ngắn hạn là đóng gate Docker trên host có engine, khóa image digests, kiểm restart/backup/restore và xác minh lại URL trước buổi bảo vệ. Demo hai phút nên chọn ba điểm kiểm chứng: câu trả lời có nguồn, trace nhiều agent và Safety veto. Không mở đầu bằng “hệ thống chẩn đoán chính xác”, không nói tự train LLM và không dùng số unit tests làm accuracy.

## 5.9. Kết luận

Đề tài đã hiện thực một hệ hỗ trợ giáo dục diabetes với DL, KG/RAG, remote LLM, RL và rules được tổ chức thành MAS có contracts, feedback, veto và persistence. Kết quả cho thấy khả năng tích hợp và audit được bằng code, trace và thực nghiệm thật; đồng thời một số baseline tốt hơn, coverage LLM sample còn hạn chế và so sánh MAS chưa tách được hiệu ứng budgets. Đó là các kết quả có ý nghĩa để bảo vệ trung thực. Nghiệm thu Phase 08 chưa hoàn tất vì Docker runtime chưa chạy; báo cáo và demo được bàn giao cùng blocker cụ thể để tiếp tục kiểm chứng.
