# Đọc báo cáo tham khảo và quyết định áp dụng

Nguồn local: `tieuluan_final_CT_03_khoipv.447.pdf`, 132 trang PDF, tác giả Phan Văn Khôi, B23DCCN447, lớp D23CTPM01-B; cùng tên học phần và giảng viên trên bìa. Đây là diễn giải từ tài liệu được người dùng cung cấp, không xác minh độc lập việc thực thi các notebook của tác giả.

Báo cáo tham khảo đi theo sáu chương: lịch sử AI; các bài toán ML (nhận xét khách hàng, diabetes large, giá nhà); CNN (MNIST/CIFAR-10); RNN (cổ phiếu/avocado); KG/RAG; agents và thí nghiệm RL/rules trong thị trường. Nội dung khác đề cương năm chương của hệ đa agent diabetes trên bảng của lớp mình. Không lấy 132 trang hoặc số lượng model của họ làm tiêu chí phải thêm vào dự án.

| Điểm đáng học | Áp dụng ở dự án mình | Không suy diễn |
|---|---|---|
| Mỗi thí nghiệm có điều kiện, baseline và giải thích kết quả | Thêm `final_mas`: workflow trực tiếp có cùng maximum 2 retrieval rounds, 2 draft rounds và 4 provider attempts với MAS | Completion cao hơn với retry budget khác chưa phải hiệu ứng decomposition |
| Phân biệt quan sát với lời giải thích | Giữ CSV từng run, seed, scope và manifest; báo cả baseline thắng/hòa | Không sao chép số liệu hay kết luận chưa chạy lại |
| Phân tích lỗi và thử điều kiện khác | Bổ sung paraphrases tiếng Việt; kiểm full workflow bilingual và schema-rejection retry | Không mô tả sáu câu đã xem như blind clinical benchmark |
| RL nhiều seed và kiểm thay đổi môi trường | Giữ ba training seeds, 300 evaluation seeds và rule comparator hiện có; nêu simulator assumptions | Không đưa market reward/policy vào y tế |
| Tổ chức code/output/giới hạn theo từng bài toán | Chuẩn bị handoff, source archive, artifact archive, một lệnh chạy native | Không trộn Pima với diabetes large của bài khác hoặc chuyển accuracy giữa datasets |

Không tái sử dụng code, dataset hoặc hình của báo cáo tham khảo. `final_baseline.py` được mở rộng từ baseline của chính dự án. Các biểu đồ mới chỉ lấy từ lần chạy thực. Kiến trúc CNN/RNN, agent cạnh tranh giá và local Qwen trong tài liệu không được thêm chỉ để giống bài tham khảo; chúng không giải quyết trực tiếp yêu cầu demo diabetes MAS hiện tại.

Kết luận cho báo cáo tổng hợp: giữ bố cục của thầy; dùng cách lập luận thực nghiệm chặt chẽ hơn. Chứng minh MAS bằng contracts, dispatch/feedback, Verifier, Safety veto, persistence và trace; không bằng số lượng module hoặc số trang.
