# CHƯƠNG 1. GIỚI THIỆU

## 1.1. Bối cảnh bài toán

Diabetes là miền phù hợp để nghiên cứu một hệ hỗ trợ có nhiều nguồn quyết định: một mô hình phân loại dữ liệu bảng cho kết quả định lượng, kho tài liệu cung cấp giải thích có nguồn, còn các giới hạn về phát ngôn và phạm vi sử dụng phải được kiểm tra riêng. Theo trang tổng quan của NIDDK [1], diabetes liên quan đến glucose máu cao; thông tin về triệu chứng, yếu tố nguy cơ, sinh hoạt và xét nghiệm được tổ chức thành nhiều chủ đề. Người đọc vì vậy cần biết câu trả lời dựa trên tài liệu nào và khi nào một câu hỏi đã vượt khỏi phạm vi giáo dục chung.

Đề tài “Diabetes Multi-Agent Intelligent Support System” xây dựng một không gian tìm hiểu về bệnh tiểu đường. Hệ thống không thu nhận hồ sơ bệnh nhân thật để demo. Các giá trị assessment do dự án soạn là SYNTHETIC; dữ liệu Pima dùng cho nghiên cứu mô hình là dữ liệu lịch sử riêng, không được đánh đồng với người đang dùng web. Đầu ra phân loại không được gọi là chẩn đoán hoặc xác suất bệnh cá nhân đã hiệu chỉnh.

## 1.2. Vấn đề cần giải quyết

Một classifier chỉ trả score và class không giải quyết được nhu cầu giải thích. Một LLM có thể diễn đạt tự nhiên nhưng câu trả lời cần được ràng buộc bởi evidence, kiểm tra citation và từ chối yêu cầu nguy hiểm. Một kết quả retrieval có URL đúng vẫn có thể không liên quan đến câu hỏi; một quote đúng nguồn vẫn chưa chứng minh claim bao quanh nó được hỗ trợ. Những khoảng cách này là vấn đề tích hợp và kiểm soát, không thể chỉ giải bằng tăng accuracy hoặc chọn model lớn hơn.

Hệ thống cần nối bốn dạng bằng chứng: output từ checkpoint đã khóa, đoạn kiến thức công khai có provenance, hành động giáo dục được phép và quyết định an toàn. Khi một dependency mất kết nối, phải xác định tác vụ nào không thể hoàn thành, giữ lại nội dung chưa được phép phát hành và lưu trace cho người kiểm tra. Không được thay một agent unavailable bằng kết quả giả để demo luôn xanh.

## 1.3. Lý do sử dụng Multi-Agent

Đề tài phân rã theo trách nhiệm có thể kiểm tra: Prediction không được tự viết lời khuyên thuốc; Knowledge không được tự phê duyệt câu trả lời; Education không được tự xác nhận citation của mình; RL không được mở rộng action space; Safety có quyền ngăn phát hành. Coordinator nhận các kết quả có kiểu, quyết định thứ tự và phản hồi có giới hạn. Phân rã này làm rõ ai được phép làm gì, vì sao được gọi và trạng thái nào dẫn tới fallback.

Lợi ích kiến trúc cần được phân biệt với ưu thế thực nghiệm. Việc có sáu agent giúp mô tả quyền hạn và kiểm tra đường đi; nó chưa tự chứng minh chất lượng tốt hơn một chương trình trực tiếp gọi cùng tools. Đề tài do đó có baseline cùng tools, lưu latency và task completion, đồng thời công khai khác biệt ngân sách retry. Chỉ kết luận trong phạm vi kết quả đo được.

## 1.4. Mục tiêu và câu hỏi nghiên cứu

Mục tiêu kỹ thuật là thực hiện workflow xuyên suốt từ React qua Coordinator tới các agent, lưu PostgreSQL và trả evidence/trace thật. Mục tiêu nghiên cứu là đánh giá thành phần và hệ thống bằng các phép đo khác nhau: phân loại trên cùng split, truy hồi trên cùng corpus/câu hỏi, policy trên cùng simulator seeds và kiểm thử an toàn trên kịch bản có expected behavior. Mục tiêu trình bày là giúp người xem lần theo một câu trả lời thay vì chỉ nhìn một số accuracy.

Ba câu hỏi nghiên cứu được dùng để tổ chức báo cáo. Thứ nhất, classifier MLP có tạo được output tái lập và có lợi thế gì so với LR/RF trên split đã khóa? Thứ hai, KG và RAG trả evidence liên quan đến mức nào, và nguồn được bảo toàn thế nào khi LLM tổng hợp? Thứ ba, các agent phối hợp ra sao khi evidence yếu, verifier từ chối hoặc Safety veto; kết quả có cải thiện hay chỉ bổ sung chi phí? Các câu hỏi này cho phép kết quả âm, không đặt sẵn kết luận MAS hoặc DL phải thắng.

## 1.5. Phạm vi

Phạm vi gồm dữ liệu bảng Pima với tám đặc trưng; MLP nhị phân; 14 trang NIDDK được snapshot; graph có assertion hỗ trợ bằng quote; encoder/reranker đa ngôn ngữ pretrained; Groq inference; Q-learning giáo dục trong simulator; rule-based Safety; giao diện tiếng Việt; persistence và demo HTTPS tạm. LLM không được train từ đầu hoặc fine-tune trong đề tài. Encoder/reranker được dùng từ model upstream có revision/manifest, không trình bày là mô hình nhóm tự huấn luyện.

Ngoài phạm vi là chẩn đoán lâm sàng, thay đổi thuốc, bệnh án thật, ước lượng nguy cơ theo dân số Việt Nam, học online từ người dùng, multi-turn memory, distributed agents và chứng nhận an toàn y tế. Không bổ sung CNN/RNN chỉ để tăng số kỹ thuật: yêu cầu trên bảng là Deep Learning phục vụ dự đoán/phân loại, không bắt buộc mọi kiến trúc học sâu trong một demo.

## 1.6. Đóng góp và giới hạn

Đóng góp chính là một implementation có thể kiểm tra: sáu agent, các hợp đồng message/state, hai cổng Safety, feedback retrieval/repair hữu hạn, provenance admission lặp lại trước công bố và commit SQL trước HTTP 201. Bộ thí nghiệm có CSV/JSON/PNG/manifest; giao diện chỉ hiển thị artifact đã kiểm tra checksum. Một gateway riêng bảo vệ bản build bằng mật khẩu và giới hạn request cho demo qua HTTPS.

Giới hạn khoa học gồm Pima hẹp, retrieval labels thô, không có đánh giá chuyên gia y tế, RL reward giả lập và baseline MAS khác ngân sách retry. Giới hạn triển khai gồm host chưa có Docker engine/WSL nên Compose runtime chưa được nghiệm thu; tunnel tạm vẫn phụ thuộc máy cá nhân. Bản báo cáo vì vậy không khẳng định hoàn thành 100% hoặc sẵn sàng triển khai y tế. Audit trước khi viết nằm ở `docs/phase08_scope_audit.md`.

## 1.7. Tổ chức báo cáo

Chương 2 trình bày agent/MAS, giao tiếp, luật và RL. Chương 3 đặc tả kiến trúc, contracts, data flow và xử lý lỗi. Chương 4 đi vào dữ liệu, DL, KG/RAG, LLM, Safety, policy và cách phối hợp. Chương 5 nối source, demo, kiểm thử và thực nghiệm, đồng thời nêu phần nghiệm thu chưa hoàn tất. Cấu trúc này theo đề cương trong ảnh bảng; cách trình bày tham khảo tiểu luận 03 của tác giả, không trộn kết quả assignment vào kết quả dự án mới.
