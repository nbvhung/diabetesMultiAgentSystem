# TÀI LIỆU THAM KHẢO

[1] National Institute of Diabetes and Digestive and Kidney Diseases. Diabetes Overview và các trang chủ đề trong corpus dự án. https://www.niddk.nih.gov/health-information/diabetes/overview . Snapshot, retrieved_at và SHA256 được lưu trong `data/knowledge/diabetes-v2`; nội dung web hiện tại có thể khác snapshot. Chính sách sử dụng: https://www.niddk.nih.gov/copyright .

[2] M. Wooldridge, N. R. Jennings (1995). Intelligent Agents: Theory and Practice. The Knowledge Engineering Review, 10(2), 115–152. Bản ghi tác giả/cơ quan: https://spiral.imperial.ac.uk/entities/publication/d1e966d6-907a-4838-a8ff-64a5992f4014 ; danh mục tác giả: https://www.cs.ox.ac.uk/people/michael.wooldridge/pubs/ . Dùng làm nền tảng khái niệm agent; không coi implementation dự án là chứng minh mọi thuộc tính lý thuyết.

[3] C. J. C. H. Watkins, P. Dayan (1992). Q-learning. Machine Learning, 8, 279–292. Bản tác giả: https://www.gatsby.ucl.ac.uk/~dayan/papers/cjch.pdf .

[4] R. S. Sutton, A. G. Barto (2018). Reinforcement Learning: An Introduction, second edition. MIT Press. Trang sách tác giả: http://incompleteideas.net/book/the-book-2nd.html . Dùng cho MDP/reward/value learning; không suy lý thuyết hội tụ thành thành tích simulator của dự án.

[5] P. Lewis et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. https://arxiv.org/abs/2005.11401 . Dùng làm nền tảng retrieval + generation, không nhận đã tái tạo quá trình train RAG trong paper.

[6] Groq. Structured Outputs và API Reference. https://console.groq.com/docs/structured-outputs ; https://console.groq.com/docs/api-reference . Tham khảo 03/11/2026; source code và experiment manifest ghi model cấu hình tại lần chạy. Schema validity không đồng nghĩa factual correctness.

[7] Pima Indians Diabetes mirror và mô tả dữ liệu. https://github.com/jbrownlee/Datasets/blob/master/pima-indians-diabetes.data.csv ; https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.names . Dataset owner được mô tả là NIDDK; license cụ thể chưa xác minh. Dự án pin SHA256 của CSV, không tự gán CC0/CC-BY.

[8] PyTorch. Start Locally. https://pytorch.org/get-started/locally/ . Tham khảo cho CPU installation; model/training implementation thực tế tại `backend/app/ml/pipeline.py`.

[9] Docker. Control startup and shutdown order in Compose. https://docs.docker.com/compose/how-tos/startup-order/ . Dùng cho health dependency và initialize job; không phải bằng chứng Docker đã chạy trên host này.

[10] Cloudflare. Quick Tunnels. https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/ . URL demo tạm phụ thuộc connector trên máy local, không có cam kết uptime hoặc cloud hosting độc lập.

[11] Model upstream cards: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 và https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 . Dự án lưu revision/file hashes khi chuẩn bị, dùng local_files_only, không train hai model này.

[12] Artifacts nội bộ dự án: `experiments/results/*.csv`, `*.json`, `*.manifest.json`; `notebooks/01..04`; `docs/validation/phase08`; `docs/report/figures/catalog.json`. Đây là nguồn của bảng/hình thực nghiệm, không phải bài báo bình duyệt. Mỗi artifact có scope riêng, không ghép các corpus khác nhau thành trước/sau.

[13] Nguyễn Bá Việt Hùng. `tieuluan03_06_13_hungnbv.pdf`, tài liệu học phần tháng 10/2026. Chỉ tham khảo bìa, chương mục, bảng/hình và cách dẫn source; không thay kết quả hệ thống mới bằng output assignment cũ.
