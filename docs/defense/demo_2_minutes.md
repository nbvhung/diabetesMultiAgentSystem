# Demo 2 phút — bản ngắn dùng trước giảng viên

## Chuẩn bị trước, không tính vào hai phút

Mở URL trong [deployment](../deployment.md), đăng nhập `demo` với password `.env.demo`; tuyệt đối không chiếu file đó. Kiểm readiness, warm một câu hỏi; mở sẵn run thực đã lưu trong [public_demo.json](../validation/phase08/public_demo.json). Máy, BE, PostgreSQL, Neo4j và tunnel phải chạy. Nếu mất internet, dùng native web và nói rõ đang demo local; nếu đọc lại run thì nói rõ là run đã thực thi, không gọi là live.

## Kịch bản nói và thao tác

| Thời điểm | Thao tác | Lời trình bày |
|---|---|---|
| 0:00–0:15 | Tổng quan; chỉ sơ đồ | “Đây là hệ đa agent hỗ trợ tìm hiểu tiểu đường. DL, KG/RAG, LLM, RL và rules là công cụ của các agent. Hệ thống không chẩn đoán.” |
| 0:15–0:55 | Khảo sát mô phỏng → Điền mẫu → xác nhận SYNTHETIC → Yếu tố nguy cơ → chạy | “Input này do dự án tạo. Prediction chạy checkpoint; Knowledge tìm evidence; RL chọn hành động giáo dục; Education tạo nội dung; Verifier và Safety kiểm trước phát hành.” |
| 0:55–1:15 | Chỉ score/model limitation, citation và link | “Score là đầu ra nghiên cứu chưa hiệu chỉnh. Nội dung đang ở chế độ llm/extractive như UI ghi. Đây là nguồn NIDDK thực được gắn với response.” |
| 1:15–1:35 | Xem hành trình; mở quyết định/metadata cần thiết | “Coordinator ghi lý do gọi từng agent, RL proposed/effective action, hai Safety gates và run ID đã lưu SQL. Đây là trace sau chạy, không phải animation tiến độ giả.” |
| 1:35–1:55 | Hỏi về tiểu đường → demo đổi insulin → gửi | “Yêu cầu đổi liều bị Safety chặn trước khi chạy các agent nghiệp vụ. Không tạo citation để hợp thức hóa một lời khuyên nguy hiểm.” |
| 1:55–2:00 | Chốt tại refusal | “Đóng góp là phối hợp có contracts, kiểm chứng và audit. MLP/RL chưa vượt mọi baseline; triển khai hiện là HTTPS tạm, Docker runtime vẫn chưa nghiệm thu.” |

Nếu câu hỏi đầu chưa xong sau khoảng 25 giây, không nhấn gửi nhiều lần. Chuyển sang tab run đã lưu và nói “Tôi mở lại kết quả của lượt đã chạy để xem đầy đủ trace”; báo thực tế pending/fallback. Không đổi label, metric hoặc nội dung output để khớp lời thoại. Không dành hai phút để cài Docker, train model hoặc mở terminal chứa secrets.
