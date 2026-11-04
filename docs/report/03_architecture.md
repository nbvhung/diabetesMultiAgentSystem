# CHƯƠNG 3. KIẾN TRÚC TỔNG QUAN

## 3.1. Requirements và mức hoàn thành

Yêu cầu chức năng gồm assessment tám feature, hỏi đáp giáo dục có nguồn, timeline agent, truy xuất run đã lưu và xem thí nghiệm thật. Yêu cầu phi chức năng gồm input validation, dependency readiness, versioned contracts, sanitization lỗi, không lưu secret vào source, không fake metrics và khởi tạo môi trường có thể lặp lại. Các ảnh yêu cầu của giảng viên nhấn mạnh MAS nối DB/DL, KB/RAG, rules và RL; báo cáo không thay trọng tâm bằng một ứng dụng dự đoán đơn lẻ.

Audit được thực hiện trước khi viết tại `docs/phase08_scope_audit.md`. Các khối nghiệp vụ đã có code và demo thật; acceptance Docker chưa đạt vì không có engine trên host. Từ đó bản báo cáo dùng trạng thái nghiệm thu cuối BLOCKED thay vì ký xác nhận toàn bộ 100%. Các phần đã chạy vẫn được ghi bằng bằng chứng độc lập, không bị xóa chỉ vì một blocker triển khai.

## 3.2. Overall architecture

![Hình 3.1. Kiến trúc tổng thể](figures/architecture.png)

Nguồn Hình 3.1: source runtime 3.0 và migrations. React không gọi model trực tiếp; API là đầu vào cho Coordinator. PostgreSQL giữ transaction/snapshots, Neo4j giữ public evidence. LLM remote không được truy cập database của ứng dụng hoặc tùy ý chọn URL/tool.

Frontend dùng React, TypeScript và Vite. API FastAPI có v2/3.0 cho workflow mới và v1/2.4 giữ tương thích lịch sử. Backend tổ chức modular monolith: schemas, agents, Coordinator, services inference, graph retrieval và repository. Deployment thêm initialize job và reverse proxy; deployment logic không sửa frozen model/policy hoặc nhãn kết quả cũ.

## 3.3. Coordinator và workflow state

Coordinator giữ results, warnings, evidence, decisions, retries và trace riêng từng run. Khi dispatch, nó tạo Message UUID, ghi TASK_DISPATCHED, thực thi theo timeout, validate Result và ghi status/duration/summary. Agent trả sai identity hoặc output/status bị chuyển thành lỗi, không đưa object chưa kiểm tra cho agent tiếp theo.

Ngân sách mặc định gồm deadline 85 giây sau warmup, tối đa hai retrieval rounds, hai draft attempts và bốn provider attempts. Timeout theo agent là Prediction 30s, Knowledge 20s, RL 3s, Education 30s, Verifier 30s, Safety 2s. Các giới hạn này chống vòng lặp không dừng; chúng không bảo đảm mọi native computation bị hủy ngay lập tức. Các service có thể giữ khóa/model chung nhưng mutable state và call budget không dùng chung giữa người dùng.

## 3.4. Message/state contracts và versioning

Input mới nhận language vi/en, question tối đa 4000 ký tự và/hoặc assessment. Assessment phải có tám trường đúng kiểu và `is_synthetic=true`. Output giữ score/model version/limitations; một warning nghiên cứu có thể làm workflow DEGRADED dù các agent hoàn thành. Không đổi status để làm demo đẹp hơn.

**Bảng 3.1. Các hợp đồng quan trọng.** Nguồn: `research/schemas.py`, `schemas/prediction.py`.

| Contract | Ràng buộc chính | Ý nghĩa |
|---|---|---|
| RunInput 3.0 | Có question hoặc assessment, extra forbidden | Ngăn payload tùy ý |
| Message | run/message UUID, recipient khớp task | Correlation và routing |
| Result | Agent/status/output đúng loại | Không nhận success giả từ stub |
| Evidence | ID/hash, URL, section, excerpt, source version | Truy nguyên nguồn |
| EducationOutput | claims/supports hoặc fallback mode rõ | Không gọi extract là LLM answer |
| VerifierOutput | verdict + candidate SHA256 | Proof gắn đúng bản nháp |
| SafetyDecision | input/output stage, rule IDs, allowed | Audit veto/fail-closed |
| Event | sequence, reason, attempt, duration, summaries | Monitor sau thực thi |

API path version, runtime schema, model version và policy version được tách biệt. Snapshot cũ không được tự gắn nhãn mới. Prediction serving 1.1 và Q-policy 1.1 giữ nguyên; v2 dùng JSON storage đã có nên không cần DDL mới sau migration 0002. Nếu format không tương thích, trả trạng thái review theo contract thay vì dựng lại output lịch sử.

## 3.5. Sequence và data flow

![Hình 3.2. Sequence của một workflow](figures/sequence.png)

Nguồn Hình 3.2: `research/api.py`, Coordinator và repositories. Mũi tên 201 nằm sau COMMIT; phản hồi trước commit sẽ tạo ấn tượng lưu thành công sai khi database lỗi. GET đọc snapshot đã lưu, không gọi lại LLM để tạo câu trả lời mới.

Đầu vào đi qua Safety trước. Với assessment, Prediction tạo record trong transaction; Knowledge truy hồi nếu có question. RL nhận actual evidence/prediction cùng education context được gắn nhãn simulated. Education tạo candidate; Verifier kiểm tra; Coordinator lặp admission và Safety output. Chỉ final response/evidence được phép mới đưa vào snapshot. Rejected drafts bị xóa khỏi summaries và không xuất bản trong monitor.

![Hình 3.3. Luồng end-to-end](figures/e2e_workflow.png)

Nguồn Hình 3.3: cùng source của Hình 3.2, biểu diễn theo chức năng để trình bày demo. Nhánh veto/fallback được giải thích trong văn bản và trace; hình tuyến tính này không mô tả mọi lỗi có thể xảy ra.

## 3.6. Failure handling

Missing model trả Prediction unavailable và không có score thay thế. Missing Neo4j làm Knowledge unavailable; không giả rằng local vector-only evidence là một graph query thành công. Evidence không đủ dẫn tới rewrite hữu hạn hoặc clarification. Provider timeout/auth/schema error chỉ tạo code sanitize và chuyển sang exact-source fallback khi có nguồn hợp lệ.

Verifier reject làm Education sửa từ reason codes; hết budget thì nguồn nguyên văn vẫn phải qua admission. Safety missing/error/veto giữ lại nội dung; action ngoài whitelist bị chặn. SQL unavailable/transaction failure trả 503 và rollback; không trả 201 kèm một run chỉ tồn tại trong RAM. Lỗi raw exception không đi ra API. Frontend hiển thị đúng mode/status và không hardcode output agents.

## 3.7. PostgreSQL

![Hình 3.4. PostgreSQL ERD](figures/erd.png)

Nguồn Hình 3.4: hai migration 0001_phase02 và 0002_phase03. `demo_cases` có check synthetic=true; assessment tham chiếu case; prediction tham chiếu assessment/model/run. `agent_events` có unique(run,sequence). JSON columns giữ full typed snapshot/result/event để đọc lại phiên bản đã lưu. Đây là sáu bảng nghiệp vụ, không phải hồ sơ bệnh án.

Native tests kiểm tra migration upgrade/downgrade trên database test riêng, persistence qua create/read, concurrent correlation và rollback. Migration test có tính phá schema nên không được trỏ vào DB demo; hai PostgreSQL test database được tách biệt. Mật khẩu chỉ lấy từ env và engine hide_parameters; không xuất URL có credentials vào báo cáo.

## 3.8. Neo4j và provenance

![Hình 3.5. Neo4j schema hiện hành](figures/neo4j_schema.png)

Nguồn Hình 3.5: `research/graph.py`. Node source → evidence khác với concept → assertion; assertion phải trỏ về quote hỗ trợ, không suy luận từ tương quan Pima. MERGE/constraints làm seed lặp lại không tăng duplicate theo cùng identity. Release binding giúp không lẫn snapshot cũ vào kết quả hiện tại.

## 3.9. Deployment và biên truy cập

Compose thiết kế bốn service chạy lâu dài: frontend nginx, backend, PostgreSQL, Neo4j; initialize là job một lần. Named volumes giữ hai database. Healthchecks và dependency conditions ngăn backend chạy trước schema/seed. Checkpoint/corpus/experiments mount read-only; không COPY `.env` vào image. Backend dùng user không phải root, frontend build nhiều giai đoạn.

Trên host hiện tại, Compose CLI parse được nhưng engine không tồn tại nên chưa build/start container. Demo HTTPS dùng phương án khác: built React + authenticated gateway local + Cloudflare Quick Tunnel. Nó đã được kiểm tra từ internet, nhưng backend/DB vẫn ở máy cá nhân. Cloud hosting độc lập được ghi NOT_COMPLETED, không dùng một URL tunnel làm bằng chứng cloud deployment.
