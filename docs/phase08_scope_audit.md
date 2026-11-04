# Đối chiếu yêu cầu giảng viên trước khi viết báo cáo

Ngày kiểm tra: 03/11/2026. Nguồn yêu cầu: hai ảnh bảng do người dùng cung cấp ngày này. Đây là phần diễn giải từ ảnh, không phải đề cương chính thức được thầy xác nhận lại bằng văn bản. Tham khảo hình thức: `tieuluan03_06_13_hungnbv.pdf`; không lấy kết quả assignment cũ làm kết quả hệ thống mới.

**Kết luận trước khi viết: chưa thể xác nhận toàn bộ đồ án hoàn thành 100%.** Các khối nghiệp vụ của đề tài đã có code và bằng chứng tích hợp; nghiệm thu đóng gói Docker còn bị chặn bởi máy không có Docker engine/WSL. Báo cáo Phase 08 phải công khai tình trạng này; bản có thể biên tập/nộp chỉ được gắn READY_FOR_DEFENSE sau khi hoàn thành gate còn thiếu. Điểm số của mô hình hoặc số agent không thay thế việc kiểm tra yêu cầu.

| Nội dung đọc được từ bảng | Đối chiếu hiện tại | Bằng chứng và giới hạn |
|---|---|---|
| Project: hệ đa agent cho bệnh tiểu đường | IMPLEMENTED, thực thi thật | Runtime v2/3.0; sáu agent với task/result và tool riêng, Coordinator có feedback và Safety veto |
| DB có sẵn → Deep Learning → dự đoán/phân loại | IMPLEMENTED | Pima 768 hàng; MLP 8→32→16→1, baseline LR/RF, notebook đã chạy; POST assessment synthetic trả score/class, ghi SQL |
| Neo4j/KB + RAG | IMPLEMENTED | 14 nguồn NIDDK, 449 chunk, 11 assertion có supporting quote; retrieval phụ thuộc graph thật; thiếu graph không tạo citation |
| Tư vấn/hỗ trợ qua agent | IMPLEMENTED trong phạm vi giáo dục | Education/Groq, Verifier, evidence links; không chẩn đoán, không cá nhân hóa liều thuốc |
| Reinforcement Learning | IMPLEMENTED trong simulator | Q-learning offline, state/action/reward có mã; serving dùng policy frozen hoặc rule fallback rõ ràng; không học online từ bệnh nhân |
| Rule-based | IMPLEMENTED | Safety đầu vào/đầu ra, whitelist hành động và chặn điều chỉnh insulin; 3 scenario mới qua HTTPS có persistence |
| Giới thiệu → hệ đa agent → kiến trúc → thành phần → code/demo | REPORT_PENDING tại thời điểm audit | Đây là bố cục 5 chương sẽ dùng; không đổi trọng tâm sang chỉ accuracy DL |
| Tiếp tục từ kiến thức project/assignment trước | Có sự kế thừa phương pháp, không nhận là tái sử dụng code chưa kiểm chứng | Các notebook mới của project có train/eval riêng; báo rõ khác biệt với assignment, không trộn dataset/metric |
| Website mở demo ngắn | HTTPS_DEMO_VERIFIED | Ba scenario qua URL HTTPS thật; backend vẫn chạy trên máy cá nhân. Không phải cloud deployment độc lập |
| Docker Compose chạy được (yêu cầu bổ sung Phase 08 của người dùng) | BLOCKED_RUNTIME | Compose CLI parse thành công; `up --build --wait` lỗi không có `//./pipe/docker_engine`; không có Docker/WSL |
| Môi trường tái lập, báo cáo/defense hoàn chỉnh | IN_PROGRESS | Cần bộ hướng dẫn, kiểm thử cuối, file DOCX/PDF và kiểm tra trình bày |

“Có đủ thành phần” không đồng nghĩa “ChatGPT chuyên khoa” hoặc “hiệu quả lâm sàng”. LLM dùng Groq API, không tự train; classifier Pima không tổng quát được sang mọi người dùng. Q-learning chưa vượt rule baseline; so sánh MAS cũ khác ngân sách retry, vì vậy không dùng nó làm bằng chứng ưu thế nhân quả. Các giới hạn này không được sửa bằng việc gọi output là chính xác.

## Điều kiện đóng audit

1. Kiểm thử backend đầy đủ trên hai PostgreSQL database và Neo4j riêng, không skip; frontend tests/build và browser workflow thật.
2. Migration, graph seed, model/policy load, RAG và demo được ghi log/kết quả.
3. Compose phải build/start, các service healthy và chạy được demo; hiện còn BLOCKED do hạ tầng host. Parse YAML chưa thỏa điều kiện này.
4. Báo cáo dẫn tới CSV/JSON/manifests, hình thật và trace; DOCX/PDF có kiểm tra render. Ít nhất 20 câu hỏi bảo vệ, script 2 phút và 5–10 phút.
5. Trạng thái cuối lấy từ [phase_status](phase_status.md) và kết quả Phase 08; không dùng trạng thái lịch sử của Phase 07 để tuyên bố Phase 08 PASS.

Tiếp tục hoàn thiện các phần không phụ thuộc Docker; báo cáo giữ mục “nghiệm thu triển khai chưa hoàn tất” nếu điều kiện 3 chưa thực thi được. Không trì hoãn toàn bộ tài liệu và demo chỉ vì blocker hạ tầng, nhưng cũng không xóa blocker khỏi bản báo cáo.
