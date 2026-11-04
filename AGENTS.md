# Quy tắc làm việc trong Diabetes MAS

- Chỉ thực hiện phạm vi người dùng đã giao. Người dùng đã yêu cầu Phase 08: triển khai demo, tái lập môi trường, báo cáo và chuẩn bị bảo vệ. Ưu tiên báo cáo bám đề cương giảng viên; kiểm tra mức hoàn thành trước khi viết và không khẳng định 100% hoặc READY_FOR_DEFENSE nếu còn tiêu chí chưa kiểm chứng.
- MAS là trọng tâm. DB, DL, Neo4j/RAG, rules và RL là công cụ phục vụ agent, không phải các dự án độc lập.
- Đọc code và phase_status trước khi sửa. Không ghi đè assignment cũ. Code tái sử dụng phải có nguồn và kiểm thử tương thích; hiện chưa tái sử dụng code assignment nào.
- Không báo stub là tích hợp; không bịa model, kết quả huấn luyện, metric, biểu đồ, evidence hay bệnh nhân thực.
- Demo và fixture phải ghi rõ SYNTHETIC. Không đưa dữ liệu bệnh nhân thật vào Git, log, notebook hay artifact.
- Không đưa ra chẩn đoán chắc chắn. Kết quả nguy cơ phục vụ giáo dục, không thay thế nhân viên y tế.
- Không lưu secret vào source. Dùng environment; .env.example chỉ chứa placeholder.
- Contract Phase 00 schema_version=1.0 bị khóa. API v1 giữ runtime 2.4/ADR 0006 và Safety policy 1.1; API v2 dùng runtime 3.0, diabetes-safety-2.0 theo ADR 0007. PredictionResult serving 1.1/ADR 0003 và artifact DL/RL không đổi. Không đổi nhãn snapshot cũ. Mọi thay đổi phá vỡ tương thích cần ADR/migration, cập nhật docs và test.
- Mỗi agent phải có trách nhiệm, input/output, chính sách quyết định, quyền tool và test riêng. Stub không được trả output nghiệp vụ hoặc success.
- Coordinator quản lý trạng thái, timeout, lỗi và trace. Safety phải fail closed khi triển khai luồng nghiệp vụ; không công bố nội dung nếu safety chưa sẵn sàng.
- Không tự mở rộng tool permissions; Phase 00 mọi enabled_tools rỗng.
- Kiểm thử thay đổi phù hợp, lưu kết quả thực tế; báo hạn chế và BLOCKED nếu điều kiện phase chưa đạt.
- Người dùng đã yêu cầu khởi tạo Git và commit source cần thiết ngày 04/11/2026. Được init/commit tại root dự án; không push khi chưa được yêu cầu. Secrets, dữ liệu/model nặng và file xuất bản phải được ignore.
