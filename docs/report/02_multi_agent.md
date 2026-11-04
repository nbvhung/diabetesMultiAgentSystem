# CHƯƠNG 2. HỆ ĐA AGENT

## 2.1. Agent và phạm vi tự chủ

Theo cách tiếp cận agent của Wooldridge và Jennings [2], tác tử được xem xét qua khả năng hoạt động tự chủ, tương tác và phản ứng theo môi trường/mục tiêu. Trong phần mềm của đề tài, “môi trường” của một agent là task có kiểu cùng tool được cấp; tự chủ là chọn cách thực hiện hoặc trả unavailable/reject trong giới hạn đó. Không yêu cầu mỗi agent phải là LLM, một tiến trình riêng hoặc có ý thức. Cũng không suy rộng rằng mọi hàm có tên Agent đều đã trở thành một MAS.

Để phân rã có ý nghĩa, cần chỉ ra trách nhiệm, input/output, policy, quyền hạn và phản ứng khi thất bại. Knowledge có thể báo evidence chưa đủ; Verifier có thể từ chối candidate; Safety có thể veto; Coordinator phải phản ứng với các kết quả này. Nếu mọi tên agent chỉ bọc cùng một prompt rồi trả success bất kể dependency, hệ thống không đáp ứng mục tiêu của đề tài. Code hiện tại kiểm tra status/output và không cho non-completed result mang output nghiệp vụ hợp lệ giả.

## 2.2. Mô hình tổ chức MAS

Hệ thống dùng kiến trúc điều phối tập trung. Coordinator là đầu mối gửi task và giữ workflow state riêng cho mỗi request. Các agent không trực tiếp gọi nhau hoặc tự tăng tool permission. Registry ánh xạ agent identity sang implementation và definition; model, graph client và Q-table là service được quản lý bởi ứng dụng, không phải các agent độc lập khác.

Đây là một modular monolith với thực thi tác vụ chủ yếu tuần tự. Đề tài không nhận là hệ phân tán, market-based negotiation hoặc autonomous multi-party deliberation. Lựa chọn này giảm phức tạp đồng bộ trong demo và làm thứ tự kiểm chứng rõ ràng. Đổi lại, Coordinator là điểm điều phối tập trung; không có bằng chứng throughput lớn, fault tolerance phân tán hoặc khả năng scale theo số agent.

![Hình 2.1. Giao tiếp tác vụ trong MAS](figures/communication.png)

Nguồn Hình 2.1: `research/schemas.py`, `agents.py`, `coordinator.py`; sơ đồ giải thích được dựng từ source, không phải phép đo. Mỗi cạnh là cặp task/result được gắn run/message ID. Sơ đồ không ngụ ý các lời gọi diễn ra đồng thời.

## 2.3. Vai trò và năng lực từng agent

Prediction nhận tám feature synthetic, gọi preprocessing và MLP đã khóa rồi ghi prediction trong transaction đang mở. Nó kiểm tra artifact version/hash; thiếu model trả unavailable, không chọn một score mặc định. Knowledge nhận câu hỏi và query bounded, truy vấn graph theo release và rank evidence; câu trả lời thiếu evidence không được tự bổ sung từ “kiến thức nhớ” của LLM.

RL Decision chọn một trong sáu hành động giáo dục đã công bố, sử dụng Q-policy hoặc rule fallback có phiên bản. Education nhận evidence và action, tạo các claim có supports hoặc exact-source fallback. Verifier có hợp đồng khác Education, kiểm tra source/quote/number/candidate hash và gọi review riêng khi có prose LLM. Safety dùng luật để kiểm tra trước xử lý và trước phát hành; quyết định của nó không được một agent khác ghi đè theo hướng dễ dãi hơn.

**Bảng 2.1. Tóm tắt quyền hạn agent.** Nguồn: `backend/app/research/agents.py`.

| Agent | Output chủ yếu | Quyền từ chối / fallback | Điều không được làm |
|---|---|---|---|
| Prediction | Score, class, model version | UNAVAILABLE khi artifact lỗi | Train, đổi threshold trong request |
| Knowledge | Evidence, coverage, adequacy | Không có evidence đủ → feedback | Tạo URL hoặc quote giả |
| RL Decision | Action, decision source, policy version | Rule fallback nếu policy thiếu | Chọn thuốc/liều điều trị |
| Education | Atomic claims, supports, mode | Extractive/clarification có nhãn | Tự phê duyệt claim của mình |
| Verifier | Verdict, reasons, candidate digest | Reject; yêu cầu repair qua Coordinator | Bỏ qua provenance vì văn phong tốt |
| Safety | Allowed, rule IDs, stage, severity | Veto / fail closed | Cho LLM vượt luật bắt buộc |

## 2.4. Giao tiếp và chia nhiệm vụ

Message chứa recipient và payload task đúng loại; result phải khớp agent và terminal status. Coordinator kiểm tra object trả về bằng schema trước khi dùng, bắt timeout/exception thành code được sanitize và ghi event. Trace có sequence và correlated run ID nên có thể tìm một quyết định trong monitor rồi đối chiếu response đã lưu.

Chia nhiệm vụ là có điều kiện: không assessment thì Prediction được SKIPPED với lý do; câu hỏi nguy hiểm bị Safety chặn sớm thì các business agent không được gọi. Thiếu question thì không cần retrieval. Evidence yếu có thể dẫn tới query rewrite lượt 2; candidate không đạt verifier có thể được compose lại từ reason codes. Những nhánh này là bằng chứng phối hợp cụ thể; không thay bằng sáu biểu tượng chạy giả trên frontend.

## 2.5. Rule-Based

Rule-based biểu diễn quyết định bằng các điều kiện có thể kiểm tra và policy ưu tiên. Trong đề tài, các luật dùng cho giới hạn phát ngôn, provenance và action allowlist. Chẳng hạn yêu cầu đổi liều insulin là một tín hiệu từ chối trước khi gọi model/LLM; nội dung chưa có evidence được phép phát hành không thể đi qua cổng công bố bằng cách gắn citation tùy ý.

Ưu điểm là khả năng kiểm tra định nghĩa và tái hiện một quyết định theo rule IDs. Nhược điểm là phụ thuộc phạm vi pattern, dễ bỏ sót cách diễn đạt chưa có và có thể chặn nhầm. Các test phân biệt câu điều kiện trong nguồn với lời khẳng định chẩn đoán cá nhân là ví dụ hiệu chỉnh phạm vi, không chứng minh luật bao phủ mọi ngôn ngữ hoặc mọi rủi ro y tế.

## 2.6. Reinforcement Learning và Q-learning

RL tối ưu tổng reward theo tương tác với môi trường; Q-learning ước lượng giá trị của state/action từ transition [3,4]. Trong dự án, environment là simulator giáo dục với hiểu biết, engagement và evidence levels giả lập. Hành động có thể là hiển thị nguồn hoặc hỏi kiểm tra hiểu; không có action kê thuốc. Reward phản ánh proxy giáo dục, không phải sức khỏe người bệnh.

Cập nhật dùng công thức: Q(s,a) ← Q(s,a) + α[r + γ max Q(s′,a′) − Q(s,a)] với target chỉ bằng r khi episode terminal hoặc hết ngân sách hữu hạn. Vì remaining budget nằm trong state, không tiếp tục bootstrap sau truncation. Các điều kiện hội tụ trong lý thuyết Q-learning không tự chứng minh policy hữu hạn của simulator đã tối ưu; các tập state chưa thăm và thay đổi phân phối vẫn cần fallback.

Rule-based và RL khác nhau ở nguồn quyết định: luật do người thiết kế chỉ định trực tiếp; Q-policy được cập nhật từ reward trong simulator. Trong serving, action mask và Safety vẫn là ràng buộc bắt buộc. Q-value cao không cho phép bỏ qua luật. Hai cách được so sánh trên cùng seeds; kết quả hiện có rule baseline tốt hơn một số chỉ số, và báo cáo giữ nguyên kết quả đó.

## 2.7. DL, KG/RAG và LLM trong MAS

DL học ánh xạ từ feature sang score; KG giữ quan hệ có cấu trúc; retrieval chọn các đoạn hỗ trợ; LLM diễn đạt từ evidence. Theo RAG [5], kết hợp retrieval với generation có thể bổ sung thông tin ngoài tham số mô hình. Implementation của dự án là một pipeline source-grounded được lắp từ các service, không phải tái huấn luyện mô hình RAG trong bài báo gốc.

Các công nghệ này là tools của agent. Score DL không tự chứng minh một claim y khoa; quan hệ graph không tự đảm bảo tất cả passage liên quan; JSON schema chỉ kiểm tra cấu trúc LLM, không đảm bảo sự thật [6]. Vì vậy có Verifier, publication admission và Safety riêng. Thiết kế không xem LLM là nguồn ground truth cuối cùng.

## 2.8. Tiêu chí đánh giá MAS

Một MAS cần được đánh giá ở cả kết quả và cơ chế. Kết quả gồm task completion, evidence relevance/provenance, safety invariants, latency và chi phí. Cơ chế gồm trace giao task, feedback, retry, veto, fallback và isolation giữa concurrent runs. Test cho tính đúng phần mềm khác phép đo chất lượng trên benchmark; cả hai phải được báo đúng mẫu số.

Đối chứng công bằng cần cùng tools, evidence, budgets và cách tính timing. Benchmark hiện có cùng quyền truy cập tools nhưng khác retrieval/repair budgets; kết quả chỉ mô tả hai cấu hình hiện hữu. Chưa có ablation matched-budget và expert answer review đủ lớn để kết luận phân rã agent tự nó tăng chất lượng. Điều này được giữ làm giới hạn nghiên cứu, không che bằng lời giới thiệu nhiều agent.
