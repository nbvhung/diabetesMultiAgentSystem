# ĐÁP ÁN ÔN TẬP VẤN ĐÁP — PHÁT TRIỂN CÁC HỆ THỐNG THÔNG MINH

Nguyễn Bá Việt Hùng · B23DCCN358 · Soạn ngày 10/11/2026

Tài liệu bám thứ tự `examination_50_questions_v2.pdf`. Đề mang tên 50 câu nhưng thực tế đánh số 1–51; tài liệu trả lời đủ 51 câu. Phần lý thuyết là lời giải thích để hiểu và trình bày; phần “Liên hệ” được đối chiếu source và artifact hiện có, không phải kết quả vừa chạy lại ngày soạn. Khi thi, trình bày ý chính trước, sau đó mở công thức, code hoặc demo nếu thầy hỏi sâu. Số liệu là kết quả nghiên cứu trên bộ ca đã lưu, không phải chứng nhận hiệu quả lâm sàng.

## I. Machine Learning và Deep Learning — câu 1–10

### Câu 1. Machine Learning là gì? Phân biệt học có giám sát, không giám sát và tăng cường

**Trả lời:** Thưa thầy, Machine Learning là cách xây dựng mô hình học quy luật từ dữ liệu hoặc tương tác, rồi dùng quy luật đó để dự đoán hay lựa chọn hành động trên tình huống mới. Thay vì viết toàn bộ điều kiện bằng tay, em xác định dữ liệu, biểu diễn, hàm mục tiêu và thuật toán học.

- **Supervised learning:** dữ liệu có cặp đầu vào–nhãn `(x,y)`; mô hình học ánh xạ `f(x) ≈ y`. Ví dụ tám đặc trưng Pima → nhãn Outcome 0/1, hoặc đặc trưng căn nhà → giá.
- **Unsupervised learning:** không có nhãn đích để học trực tiếp; tìm cấu trúc, nhóm hoặc biểu diễn. Ví dụ phân cụm khách hàng theo hành vi mua sắm. Đây là ví dụ phương pháp, không phải tuyên bố em đã tích hợp clustering vào MAS.
- **Reinforcement learning:** agent quan sát trạng thái, chọn hành động, nhận thưởng và học chính sách nhằm tăng tổng thưởng dài hạn. Ví dụ trong project, Q-learning chọn hành động giáo dục như hiển thị bằng chứng hoặc yêu cầu làm rõ trong môi trường mô phỏng.

**Chốt:** DL là một nhóm phương pháp ML sử dụng mạng nhiều lớp; RL là cách học từ tương tác và có thể kết hợp DL, nhưng Q-learning của project dùng bảng Q.

### Câu 2. Quy trình phát triển một mô hình dự đoán ML

**Trả lời:** Em đi theo chuỗi: xác định bài toán và metric → thu thập, kiểm nguồn dữ liệu → khảo sát → chia train/validation/test → xử lý thiếu, mã hóa, chuẩn hóa và tạo đặc trưng → huấn luyện → chọn cấu hình bằng validation → đánh giá cuối trên test → đóng gói và giám sát khi phục vụ.

Train dùng học tham số; validation chọn checkpoint và siêu tham số; test chỉ đánh giá sau khi các lựa chọn đã được khóa. Median, scaler và bộ chọn đặc trưng phải fit trên train rồi dùng `transform` cho validation/test. Nếu fit trên toàn bộ dữ liệu, thông tin test có thể rò rỉ vào quá trình học. Chuỗi thời gian cần chia theo thời gian, không xáo trộn tùy tiện.

**Liên hệ:** MLP Pima chia phân tầng 537/115/116, seed 42. Năm trường có số 0 không hợp lý được coi là thiếu; median imputer và StandardScaler chỉ fit trên train. Checkpoint epoch 24 được chọn theo validation BCE; test không dùng để chọn mô hình. Xem `docs/data_card.md`, `docs/model_card.md` và `experiments/results/phase02/`.

**Nguồn đối chiếu:** [scikit-learn — tránh data leakage](https://scikit-learn.org/stable/common_pitfalls.html).

### Câu 3. Phân loại khác hồi quy như thế nào?

**Trả lời:** Phân loại dự đoán một lớp rời rạc, chẳng hạn Outcome 0 hoặc 1. Hồi quy dự đoán đại lượng liên tục, chẳng hạn giá đóng cửa phiên sau hoặc giá căn nhà. Cả hai có thể dùng mạng neural nhưng khác đầu ra, loss và metric.

| Bài toán | Đích | Đầu ra thường dùng | Loss và đánh giá |
|---|---|---|---|
| Diabetes | Nhãn âm/dương theo dataset | Logit → sigmoid → score; ngưỡng tạo lớp | BCE; precision, recall, F1, ROC-AUC |
| Chứng khoán | Giá đóng cửa phiên tiếp theo | Một giá trị thực | MSE/MAE; MAE, RMSE, R² |
| Giá nhà | Giá bán | Một giá trị thực | MSE/MAE; MAE, RMSE, R² |

Score sigmoid chưa được hiệu chỉnh không tự động là xác suất nguy cơ cá nhân chính xác. Nhãn dự đoán Pima cũng không phải chẩn đoán cho người nhập thông số.

### Câu 4. Kiến trúc Artificial Neural Network

**Trả lời:** ANN có lớp đầu vào nhận đặc trưng, một hoặc nhiều lớp ẩn biến đổi biểu diễn và lớp đầu ra trả dự đoán. Với lớp thứ `l`:

`z[l] = W[l] a[l−1] + b[l]`, `a[l] = φ(z[l])`.

Weight `W` xác định mức ảnh hưởng giữa các neuron; bias `b` dịch chuyển ngưỡng đáp ứng. Hàm kích hoạt như ReLU tạo tính phi tuyến; nếu chỉ ghép các lớp tuyến tính thì toàn mạng vẫn tương đương một phép biến đổi tuyến tính.

**Liên hệ:** MLP trong MAS có cấu trúc **8 → 32 → 16 → 1**, dùng ReLU và dropout 0.15. Tám đầu vào là đặc trưng Pima; một đầu ra là logit cho phân loại nhị phân. Khi phục vụ mới lấy sigmoid để tạo score và áp ngưỡng 0.5. Không gọi lớp ẩn là từng luật y khoa: weight là tham số học từ dữ liệu, không phải quan hệ nhân quả đã xác nhận.

### Câu 5. Forward propagation và backpropagation

**Trả lời:** Forward propagation đưa đầu vào qua từng lớp để tính đầu ra và loss. Backpropagation dùng quy tắc dây chuyền để tính đạo hàm loss theo từng tham số, bắt đầu từ đầu ra và truyền ngược về các lớp trước. Optimizer dùng gradient để cập nhật tham số.

`∂L/∂W[l] = (∂L/∂z[l]) (a[l−1])ᵀ` cho một mẫu theo quy ước vector cột; với batch cần cộng hoặc lấy trung bình phù hợp với loss. Gradient descent cập nhật `θ ← θ − η∇θL`.

Trong PyTorch, thứ tự train cơ bản là:

```python
optimizer.zero_grad()
logits = model(x)
loss = criterion(logits, y)
loss.backward()
optimizer.step()
```

`zero_grad()` tránh cộng dồn gradient ngoài ý muốn. Backpropagation tính gradient; `optimizer.step()` mới thực hiện cập nhật. Khi inference em dùng `eval()` và `inference_mode()`, không gọi backward, không học lại trên dữ liệu người dùng.

### Câu 6. Loss function; MSE, BCE và Categorical Cross-Entropy

**Trả lời:** Loss đo mức sai trên dữ liệu và là mục tiêu để optimizer tối thiểu hóa. Loss huấn luyện không nhất thiết trùng metric cuối cùng.

- **MSE:** `L = (1/N)Σ(yᵢ−ŷᵢ)²`, phù hợp hồi quy; sai số lớn bị phạt mạnh. Ví dụ giá nhà hoặc giá cổ phiếu.
- **Binary Cross-Entropy:** `L = −(1/N)Σ[yᵢ ln pᵢ + (1−yᵢ) ln(1−pᵢ)]`, cho phân loại nhị phân. Trong công thức, `pᵢ` là đầu ra sigmoid.
- **Categorical Cross-Entropy:** `L = −(1/N)ΣᵢΣₖ yᵢₖ ln pᵢₖ`, cho các lớp loại trừ nhau như phân loại ảnh mèo/chó/chim, thường kết hợp softmax.

**Liên hệ:** MLP dùng `BCEWithLogitsLoss`, truyền **logit trực tiếp** vào loss; hàm này kết hợp sigmoid và BCE ổn định số. Không sigmoid thêm trước loss. Với `CrossEntropyLoss` của PyTorch, đầu vào thường là logits và target là chỉ số lớp, không softmax trước.

**Đối chiếu API:** [BCEWithLogitsLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html), [CrossEntropyLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html).

### Câu 7. Gradient Descent và vai trò learning rate

**Trả lời:** Gradient Descent cập nhật tham số theo hướng ngược gradient để giảm loss: `θₜ₊₁ = θₜ − η∇L(θₜ)`.

- **Batch GD:** mỗi bước dùng toàn bộ train; gradient ít nhiễu nhưng tốn bộ nhớ và mỗi bước có thể chậm.
- **SGD:** theo định nghĩa cơ bản, mỗi bước dùng một mẫu; cập nhật thường xuyên nhưng nhiễu.
- **Mini-batch GD:** mỗi bước dùng một nhóm mẫu; cân bằng độ ổn định và hiệu quả tính toán. Trong thực tế từ SGD cũng thường được dùng cho optimizer chạy theo mini-batch.

Learning rate `η` quyết định độ lớn bước cập nhật. Quá cao có thể dao động hoặc phân kỳ; quá thấp học chậm, có thể chưa đạt nghiệm tốt trong ngân sách cho phép. Adam dùng trung bình trượt của gradient và bình phương gradient để điều chỉnh bước theo tham số, không đồng nghĩa tự chọn mọi siêu tham số tối ưu.

**Liên hệ:** MLP dùng Adam, learning rate 0.001, batch size 32. Cấu hình nằm trong model card và artifact training config.

### Câu 8. Overfitting, underfitting và cách kiểm soát

**Trả lời:** Overfitting xảy ra khi mô hình khớp train quá mức nhưng tổng quát kém; thường thấy train loss tiếp tục giảm trong khi validation loss tăng. Underfitting là mô hình chưa học đủ cấu trúc, khiến cả train và validation đều kém. Có thể do mô hình quá đơn giản, đặc trưng yếu hoặc huấn luyện chưa đủ.

Train học tham số; validation hỗ trợ lựa chọn; test đánh giá cuối. Regularization như L2 hạn chế độ lớn weight; dropout bỏ ngẫu nhiên một phần activation khi train; early stopping dừng khi validation không cải thiện và khôi phục checkpoint tốt nhất. Đây là biện pháp giảm overfitting, không bảo đảm loại bỏ hoàn toàn.

**Liên hệ:** Em dùng dropout 0.15, tối đa 200 epochs, patience 20 và min_delta 1e−5. Lần train thực chạy 44 epochs; checkpoint tốt nhất ở epoch 24. Khi inference, `eval()` tắt cơ chế dropout ngẫu nhiên. Test 116 mẫu còn nhỏ nên cần thêm đánh giá ngoài tập hiện tại.

### Câu 9. Đánh giá phân loại và vì sao accuracy có thể gây hiểu nhầm

**Trả lời:** Với nhãn dương là Outcome=1, confusion matrix gồm TP, TN, FP và FN. Các chỉ số:

`Accuracy = (TP+TN)/(TP+TN+FP+FN)`.

`Precision = TP/(TP+FP)`; `Recall = TP/(TP+FN)`; `F1 = 2PR/(P+R)` khi mẫu số khác 0.

Precision hỏi “trong số dự đoán dương, đúng bao nhiêu”; recall hỏi “trong số nhãn dương thực, tìm ra bao nhiêu”. Nếu dữ liệu có 95% âm, mô hình luôn dự đoán âm vẫn có accuracy 95% nhưng recall dương bằng 0. Vì vậy em xem thêm confusion matrix, PR/AP, ROC-AUC và đặc tính sai âm/sai dương.

**Liên hệ:** MLP test có **TP=22, TN=66, FP=9, FN=19**. Accuracy 0.758621; precision 0.709677; recall 0.536585; F1 0.611111. Bỏ sót 19/41 nhãn dương là hạn chế rõ ràng. Không nói accuracy 75.86% nghĩa là mô hình đủ dùng để khám bệnh.

### Câu 10. So sánh mô hình phân loại, hồi quy và khó khăn triển khai DL

**Trả lời:** Phân loại trả lớp/score cho các nhóm; hồi quy trả số liên tục có đơn vị. Chọn loss, đầu ra và metric theo bài toán: BCE và F1 cho nhị phân; MSE/MAE và RMSE cho dự báo số. Giá trị RMSE ở hai tập có đơn vị khác nhau không thể so trực tiếp để kết luận bài nào tốt hơn.

Triển khai cần giữ đúng thứ tự đặc trưng, đơn vị và preprocessing như lúc train; nạp đúng checkpoint; kiểm input và NaN; quản lý CPU/GPU, latency, bộ nhớ, concurrency và lỗi phụ thuộc. Cần version artifact, API schema, logging có kiểm soát, bảo mật và theo dõi drift.

**Liên hệ:** Frontend gửi tám trường có tên; FastAPI kiểm schema; Prediction Agent gọi service đã kiểm checksum, dùng preprocessing train-fitted và checkpoint đóng băng. Thiếu hoặc sai artifact trả unavailable thay vì dùng model khác âm thầm. Thách thức cuối cùng là dữ liệu thực khác Pima; API chạy thành công không chứng minh mô hình tổng quát tốt.

## II. CNN, RNN và LSTM — câu 11–18

### Câu 11. Kiến trúc CNN và các thành phần

**Trả lời:** CNN dùng bộ lọc cục bộ trượt trên đầu vào để tạo feature map. Một cấu trúc thường gặp là input → convolution → activation → pooling → các lớp trích xuất tiếp theo → flatten hoặc global pooling → dense → output.

Convolutional layer chứa các kernel học được; mỗi kernel dò một kiểu mẫu. Feature map biểu diễn mức đáp ứng của kernel tại các vị trí. ReLU tạo phi tuyến; pooling tổng hợp vùng lân cận, giảm kích thước và chi phí. Dense cuối kết hợp đặc trưng để phân loại hoặc hồi quy. Pooling là lựa chọn thiết kế, không bắt buộc mọi CNN đều phải có.

**Liên hệ chính xác:** Assignment_04 của em dùng **Conv1D trên dữ liệu bảng**, với chuỗi lớp Conv1D → ReLU → Conv1D → ReLU → Pool → Flatten → Dense. Đây không phải ứng dụng phân loại ảnh Conv2D. Project MAS hiện dùng MLP; em không tuyên bố CNN đã được tích hợp làm Prediction Agent.

### Câu 12. Phép convolution; kernel, stride, padding và số filters

**Trả lời:** Ở mỗi vị trí, kernel nhân từng phần tử với vùng đầu vào tương ứng, cộng các tích và bias để tạo một phần tử feature map. Với nhiều kênh, tổng còn chạy trên chiều kênh. Thư viện DL thường thực hiện cross-correlation, không lật kernel như định nghĩa convolution toán học cổ điển.

Kích thước đầu ra theo một chiều:

`L_out = floor((L_in + 2P − D(K−1) − 1)/S) + 1`.

`K` là kernel size, `S` stride, `P` padding và `D` dilation. Với dilation=1, đầu vào dài 8, kernel 3, stride 1, không padding thì đầu ra dài 6. Padding 1 giữ chiều dài 8. Tăng stride thường giảm độ phân giải. Số filters quyết định số kênh đầu ra; nhiều filters tăng khả năng biểu diễn và chi phí.

Số tham số Conv2D có bias, groups=1: `C_out × (C_in × K_h × K_w + 1)`. Weight được dùng chung ở nhiều vị trí nên số tham số không tăng theo toàn bộ kích thước ảnh như dense.

### Câu 13. Vì sao CNN phù hợp phân loại ảnh?

**Trả lời:** Ảnh có cấu trúc không gian: pixel gần nhau thường liên quan và cùng một mẫu có thể xuất hiện ở nhiều vị trí. CNN khai thác kết nối cục bộ và chia sẻ trọng số, nhờ đó học hiệu quả hơn dense thuần khi xử lý ảnh lớn.

Ở lớp đầu, bộ lọc có thể học cạnh và biến đổi cường độ; các lớp sâu kết hợp thành texture, bộ phận và biểu diễn phục vụ nhận dạng đối tượng. Đây là xu hướng thường gặp, không phải mọi filter đều có ý nghĩa nhìn thấy rõ. Convolution tạo tính tương đương theo dịch chuyển trong các điều kiện thích hợp; pooling/aggregation có thể giúp giảm nhạy với dịch chuyển nhỏ, chứ không bảo đảm bất biến với mọi xoay, co giãn hay thay đổi nền.

**Liên hệ:** Với dữ liệu bảng Pima, thứ tự các cột không có cấu trúc không gian tự nhiên như ảnh. Conv1D trên bảng là thực nghiệm học phần, không có căn cứ mặc định phải tốt hơn MLP hoặc Logistic Regression.

### Câu 14. Quy trình xây ứng dụng phân loại ảnh bằng CNN

**Trả lời:** Đầu tiên em xác định lớp ảnh, thu thập và kiểm nhãn, chia train/validation/test sao cho ảnh cùng đối tượng hoặc gần trùng không rơi vào nhiều tập. Sau đó resize đúng kích thước, chuẩn hóa kênh màu, augmentation trên train, xây CNN hoặc fine-tune mô hình pretrained, huấn luyện và chọn checkpoint bằng validation.

Đánh giá test bằng confusion matrix, precision/recall/F1 theo lớp; kiểm lỗi trên điều kiện ánh sáng, góc chụp và nền khác nhau. Khi deploy, backend giải mã ảnh, kiểm định dạng/kích thước, áp đúng preprocessing, chạy `eval()` rồi trả nhãn và score. Cần giới hạn dung lượng upload, kiểm ảnh hỏng và version model. Không augmentation ngẫu nhiên vào test để báo một lần đo thiếu kiểm soát.

**Phạm vi của em:** Đây là quy trình thiết kế cho ảnh. Bài CNN thực tế của em dùng Conv1D dữ liệu bảng, không có bộ ảnh để chứng minh đã triển khai pipeline ảnh này. Khi thầy hỏi demo, em mở notebook Conv1D hiện có và giải thích khác biệt.

### Câu 15. RNN, hidden state và truyền thông tin trong chuỗi

**Trả lời:** RNN xử lý dữ liệu theo thứ tự và dùng hidden state mang thông tin từ các bước trước. Một RNN cơ bản:

`h_t = tanh(W_xh x_t + W_hh h_(t−1) + b_h)`; `ŷ_t = W_hy h_t + b_y`.

Cùng bộ trọng số được dùng qua các thời điểm. `h_t` là biểu diễn học được của lịch sử, không phải bản sao đầy đủ mọi giá trị quá khứ. Có thể dùng đầu ra cuối cho dự báo một giá trị hoặc tạo đầu ra ở từng bước. Huấn luyện dùng backpropagation through time sau khi trải mạng theo chiều thời gian.

**Liên hệ:** Assignment_06 dự báo close AAPL phiên kế tiếp từ **30 phiên OHLCV**. Một batch có dạng `[batch, 30, 5]` với cấu hình batch-first. Đây là one-step forecasting: mỗi dự đoán dùng lịch sử thực đã quan sát, không phải mô hình tự dự báo nhiều bước liên tiếp rồi coi các dự báo trước là dữ liệu thật.

### Câu 16. Vanishing gradient và exploding gradient trong RNN

**Trả lời:** Khi backpropagation qua nhiều thời điểm, gradient chứa tích nhiều Jacobian. Nếu độ lớn tích co dần thì gradient về các bước xa gần bằng 0: mạng khó học phụ thuộc dài hạn. Nếu tích tăng mạnh, gradient có thể rất lớn, làm cập nhật mất ổn định hoặc xuất hiện NaN.

Vanishing không chỉ do chuỗi dài mà còn liên quan activation bão hòa và tính chất ma trận trọng số. Exploding có thể được kiểm soát bằng gradient clipping: giới hạn norm gradient trước optimizer step. LSTM/GRU giúp luồng thông tin dài hạn nhờ cổng và đường cập nhật trạng thái; khởi tạo phù hợp, chuẩn hóa và truncated BPTT cũng có thể hữu ích tùy bài.

**Chốt khi hỏi sâu:** Clipping chủ yếu xử lý gradient quá lớn, không trực tiếp chữa gradient đã biến mất. LSTM cải thiện khả năng học phụ thuộc xa nhưng không bảo đảm mọi chuỗi dài đều học tốt; vẫn phải kiểm nghiệm trên dữ liệu và baseline.

### Câu 17. Kiến trúc LSTM và vai trò các cổng

**Trả lời:** LSTM có cell state `c_t` và hidden state `h_t`. Các cổng sigmoid tạo hệ số 0–1 để điều chỉnh lượng thông tin đi qua:

`f_t = σ(W_f[x_t,h_(t−1)] + b_f)` — forget gate quyết định giữ bao nhiêu cell cũ.

`i_t = σ(W_i[x_t,h_(t−1)] + b_i)` — input gate điều chỉnh lượng thông tin mới.

`g_t = tanh(W_g[x_t,h_(t−1)] + b_g)` — nội dung mới ứng viên.

`c_t = f_t ⊙ c_(t−1) + i_t ⊙ g_t`.

`o_t = σ(W_o[x_t,h_(t−1)] + b_o)`; `h_t = o_t ⊙ tanh(c_t)`.

Forget gate lọc trí nhớ cũ; input gate đưa thông tin mới vào; output gate quyết định phần cell state bộc lộ thành hidden state. Phép cộng trong cập nhật cell hỗ trợ truyền gradient qua thời gian, dù vẫn chịu tác động của gate và các đường đạo hàm khác.

**Liên hệ:** Em dùng LSTM để giải thích và so sánh kiến trúc; artifact chứng khoán được đối chiếu cho tài liệu này là **RNN**, không đổi tên thành LSTM.

### Câu 18. So sánh RNN, LSTM và CNN; áp dụng chứng khoán

| Kiến trúc | Điểm mạnh | Giới hạn | Phù hợp |
|---|---|---|---|
| CNN | Mẫu cục bộ, chia sẻ weight, dễ song song theo vị trí | Receptive field phụ thuộc kiến trúc; cần cấu trúc lân cận có ý nghĩa | Ảnh; Conv1D cho mẫu chuỗi |
| RNN | Biểu diễn tuần tự, trạng thái gọn | Khó học phụ thuộc xa, tính theo thời gian khó song song | Chuỗi có phụ thuộc ngắn/vừa |
| LSTM | Cổng kiểm soát trí nhớ, hỗ trợ phụ thuộc dài hơn | Nhiều tham số/tính toán, vẫn có thể overfit | Chuỗi thời gian, ngôn ngữ |

**Trả lời:** Chứng khoán là chuỗi có thứ tự nên RNN/LSTM có thể khai thác lịch sử, nhưng phù hợp về cấu trúc không có nghĩa chắc chắn dự báo tốt. Phải chia theo thời gian, scaler fit trên train và so baseline “giá ngày mai bằng hôm nay”.

**Kết quả thật:** Trong `Assignment_06/model/D2_stock/comparison.csv`, RMSE persistence khoảng **2.0821**, PyTorch RNN **13.5993**, Keras RNN **16.1933**. Lần chạy này RNN kém baseline rõ rệt. Em cần kiểm phân phối theo thời gian, cách scaling, tuning chỉ trên validation và walk-forward evaluation; chưa được kết luận nguyên nhân cụ thể nếu chưa thí nghiệm. R² cao của persistence trên mức giá cũng không tự chứng minh dự báo hướng hay lợi nhuận tốt.

## III. Knowledge Graph, Neo4j và RAG — câu 19–28

### Câu 19. Knowledge Graph là gì? Entity, relationship, property

**Trả lời:** Knowledge Graph biểu diễn tri thức qua các thực thể và quan hệ có ngữ nghĩa. Entity là đối tượng hoặc khái niệm, như diabetes, thirst hoặc một nguồn tài liệu. Relationship nối các thực thể và nêu ý nghĩa, như `HAS_SYMPTOM`. Property/attribute mô tả thực thể hay quan hệ, như tên, URL, phiên bản hoặc ngày lấy nguồn; trong property graph hai từ này thường cùng chỉ thuộc tính.

Ví dụ `(diabetes)-[:HAS_SYMPTOM]->(thirst)`. Muốn dùng quan hệ đáng tin, em cần lưu nguồn hỗ trợ, đoạn trích và version thay vì chỉ có một cạnh không giải thích được.

**Liên hệ:** Graph runtime có `DiabetesConcept`, `DiabetesAssertion`, `DiabetesEvidence`, `DiabetesSource`, `DiabetesTopic`. Assertion là một node trung gian giúp mô tả subject–predicate–object cùng bằng chứng. Graph không tự biến mọi liên kết thành quan hệ nhân quả hay kết luận bệnh của một cá nhân.

### Câu 20. Subject–predicate–object và ít nhất năm triples

**Trả lời:** Một triple gồm chủ thể, vị từ và đối tượng: “ai/cái gì — có quan hệ gì — với ai/cái gì”. Ví dụ các triple đang có trong bộ luật trích xuất của project:

1. `(type2, HAS_RISK_FACTOR, obesity)`.
2. `(type2, HAS_RISK_FACTOR, family_history)`.
3. `(type2, HAS_RISK_FACTOR, physical_inactivity)`.
4. `(diabetes, HAS_SYMPTOM, thirst)`.
5. `(diabetes, HAS_SYMPTOM, frequent_urination)`.
6. `(diabetes, SCREENED_WITH, a1c)`.

**Liên hệ:** Các quan hệ chỉ được đưa vào khi clause đã tuyển chọn xuất hiện đúng trong đoạn thuộc nguồn và section quy định. Bộ hiện có 11 assertion được hỗ trợ từ corpus. Trong property graph, triple có thể là một cạnh trực tiếp, đồng thời có assertion node để đính provenance; không bắt buộc graph này phải là RDF hoặc chạy SPARQL.

**Thao tác:** Mở `backend/app/research/graph.py`, xem `ASSERTIONS`, sau đó chạy truy vấn đầu trong `kb_diabetes_queries.cypher` để đối chiếu triple với quote và URL.

### Câu 21. Neo4j và property graph model

**Trả lời:** Neo4j là hệ quản trị cơ sở dữ liệu đồ thị. Trong property graph, node có label và các property; relationship có type, hướng và property. Một node có thể mang nhiều label; relationship nối hai node xác định. Ví dụ node `DiabetesEvidence` chứa `id`, `text`, `url`, `release`; cạnh `SUPPORTED_BY` nối assertion tới passage.

Index hỗ trợ tìm node bắt đầu theo thuộc tính; constraint như unique ID hỗ trợ toàn vẹn. Sau khi xác định điểm bắt đầu, truy vấn có thể đi theo quan hệ để tìm thông tin liên quan. Hiệu năng còn phụ thuộc mô hình dữ liệu, index, số nhánh và kế hoạch truy vấn; không khẳng định graph luôn nhanh hơn SQL.

**Liên hệ:** PostgreSQL lưu run, prediction và trace; Neo4j lưu cấu trúc tri thức và provenance. Hai database phục vụ hai nhu cầu khác nhau. File `kb_diabetes.cypher` là script tái dựng graph, không phải một instance Neo4j, cũng không bao gồm toàn bộ model embedding.

### Câu 22. Cypher: tạo Patient, Disease, relationship và truy vấn

**Trả lời:** Cypher là ngôn ngữ khai báo dựa trên pattern. Node viết bằng `(n:Label)`, quan hệ bằng `-[r:TYPE]->`; `MATCH` tìm, `WHERE` lọc, `RETURN` trả, `CREATE` tạo, `MERGE` tìm hoặc tạo pattern khi chưa có.

Ví dụ dưới đây chỉ là **SYNTHETIC**, thực hiện trong database thực hành riêng. Quan hệ biểu diễn chủ đề hỏi, không khẳng định bệnh:

```cypher
MERGE (p:Patient {id:'SYNTHETIC_P001'})
SET p.is_synthetic=true, p.age=45
MERGE (d:Disease {id:'diabetes'})
SET d.name='Diabetes'
MERGE (p)-[:ASKS_ABOUT]->(d);

MATCH (p:Patient {id:'SYNTHETIC_P001'})-[r:ASKS_ABOUT]->(d:Disease)
RETURN p.id AS patient, type(r) AS relationship, d.name AS topic;
```

Trong ứng dụng thật, truyền tham số thay vì nối chuỗi input vào Cypher; dùng constraint ID nếu cần uniqueness. `MERGE` toàn pattern không có nghĩa tự bảo đảm mọi dạng duy nhất khi chạy đồng thời nếu thiếu constraint thích hợp.

**Phân biệt:** Runtime KB hiện không có graph hồ sơ Patient; ví dụ này trả đúng yêu cầu lý thuyết của đề. [Đối chiếu CREATE/MERGE](https://neo4j.com/docs/cypher-manual/current/clauses/create/).

### Câu 23. Thiết kế KG cho diabetes

**Trả lời:** Em phân biệt dữ liệu cá nhân và kiến thức chung. Một thiết kế tổng quát có Patient, Measurement, Symptom, RiskFactor, Disease/Condition, Recommendation, Evidence và Source. Patient có measurement được gắn loại, giá trị, đơn vị và thời điểm; tài liệu kiến thức nối Disease tới symptom/risk factor và mỗi nhận định có nguồn.

Các quan hệ có thể là Patient → HAS_MEASUREMENT → Measurement; Disease → HAS_SYMPTOM → Symptom; Disease → HAS_RISK_FACTOR → RiskFactor; Recommendation → SUPPORTED_BY → Evidence → nguồn. Không suy `HAS_SYMPTOM` của bệnh thành `HAS_DISEASE` cho người có triệu chứng. Khuyến nghị cá nhân cần chính sách và thẩm quyền riêng.

**Hiện thực của em:** KB thực tập trung tri thức chung: 14 nguồn, 449 evidence, topic/concept và 11 assertion. Synthetic assessment được lưu PostgreSQL; chưa có Patient/Measurement/Recommendation đầy đủ trong Neo4j. Em trình bày phần này như thiết kế mở rộng, còn demo dùng schema đang thực thi.

### Câu 24. Truy hồi và reasoning nhiều quan hệ bằng Neo4j

**Trả lời:** Neo4j hỗ trợ truy vấn pattern để nối thông tin qua nhiều cạnh. Ví dụ từ khái niệm type2 đi tới assertion, tới đoạn bằng chứng và ngược tới source:

```cypher
MATCH p=(:DiabetesConcept {id:'type2'})
  -[:SUBJECT_OF]->(:DiabetesAssertion)
  -[:SUPPORTED_BY]->(:DiabetesEvidence)
  <-[:HAS_CHUNK]-(:DiabetesSource)
RETURN p LIMIT 25;
```

Truy vấn cho biết nhận định nào liên quan type2 và được tài liệu nào hỗ trợ. Khi muốn giới hạn release, gắn biến cho assertion/evidence và lọc `release` theo manifest hiện hành. Không chạy traversal không giới hạn trên graph lớn.

“Reasoning” có thể gồm pattern/rule do mình định nghĩa. Neo4j không tự động suy luận mọi quan hệ y khoa đúng. Hệ thống hiện dùng topic → evidence để lấy candidates và assertion để giải thích provenance; truy vấn nhiều bước trên đây phục vụ demo cấu trúc, chưa phải bộ suy luận chẩn đoán nhiều bước.

### Câu 25. RAG là gì? Vì sao kết hợp retrieval và LLM?

**Trả lời:** Retrieval-Augmented Generation là cách truy hồi thông tin từ kho ngoài rồi đưa phần liên quan vào ngữ cảnh để mô hình sinh trả lời. Retrieval cung cấp bằng chứng cụ thể; LLM diễn đạt, tổng hợp và tổ chức câu trả lời theo câu hỏi.

Kho ngoài có thể được cập nhật mà không phải train lại toàn bộ LLM. Hệ thống có thể gắn nguồn để người đọc kiểm tra. Tuy nhiên nếu truy hồi sai, nguồn lỗi hoặc mô hình suy diễn vượt nguồn, RAG vẫn có thể trả lời sai; có citation không đồng nghĩa claim được hỗ trợ.

**Liên hệ:** Knowledge Agent lấy evidence từ corpus/Neo4j, Education gọi LLM qua Groq để soạn claim có quote/ID; Verifier và Safety kiểm trước công bố. Nếu chỉ ghép trích đoạn nguồn thì phải ghi extractive, không gọi đó là LLM sinh thành công. RAG khác fine-tuning: RAG bổ sung ngữ cảnh khi trả lời; fine-tuning cập nhật trọng số.

**Nguồn:** [Lewis và cộng sự — bài báo RAG](https://arxiv.org/abs/2005.11401).

### Câu 26. Kiến trúc RAG từ ingestion tới generation

**Trả lời:** Có hai đường chính: chuẩn bị kho và trả lời truy vấn.

**Chuẩn bị:** chọn nguồn → lấy snapshot → làm sạch → chia chunk giữ ngữ cảnh → lưu metadata → tính embedding → xây index, đồng thời lưu graph nếu dùng. Metadata cần ID, nguồn, thời gian, section và version.

**Trả lời:** nhận câu hỏi → kiểm phạm vi → tạo biểu diễn truy vấn → tìm candidates bằng lexical/vector/graph → rerank → chọn top-k đủ liên quan → đưa evidence vào prompt → sinh → kiểm claim/citation → Safety → trả lời hoặc từ chối/hỏi rõ.

**Liên hệ:** Project đọc nguồn NIDDK allowlist; chunks theo câu/đoạn, nhóm khoảng tối đa 550 ký tự theo logic parser, loại câu quá dài và nội dung không được nhận. Dùng multilingual MiniLM, vector 384 chiều và cross-encoder reranker. Vector index hiện là ma trận local phục vụ similarity, **không phải Neo4j vector index**. Snapshot/chunks/manifest có checksum, runtime không tự tải nguồn/model trong request. Nếu thiếu bằng chứng không cố lấp đầy top-k bằng đoạn không liên quan.

### Câu 27. So sánh keyword, vector similarity và KG retrieval

| Cách | Dựa vào | Ưu điểm | Hạn chế |
|---|---|---|---|
| Keyword/lexical | Từ xuất hiện, TF-IDF/BM25 tùy hệ | Dễ giải thích, rẻ, tốt với thuật ngữ chính xác | Khó với diễn đạt lại và khác ngôn ngữ |
| Vector | Khoảng cách/độ tương tự embedding | Bắt gần nghĩa, hỗ trợ paraphrase | Có thể gần chủ đề nhưng sai nội dung; phụ thuộc encoder |
| KG | Thực thể, quan hệ, topic và đường đi | Kiểm cấu trúc, provenance, ràng buộc miền | Cần xây schema/liên kết; graph thiếu thì bỏ sót |

**Liên hệ:** Lexical của em dùng TF-IDF; graph lọc evidence theo topic; semantic dùng multilingual embedding; hybrid kết hợp điểm và reranker. Chế độ graph hiện vẫn dùng lexical/topic overlap để xếp hạng sau khi lấy candidates, không phải thuật toán suy luận thuần graph. Các chế độ còn phụ thuộc tập evidence đăng ký trong Neo4j.

**Chốt:** Không có cách luôn tốt nhất. Cần cùng bộ câu hỏi, nhãn relevant và ngân sách để đánh giá recall/precision/MRR cùng latency. Các score retrieval là tín hiệu xếp hạng, không phải xác suất câu trả lời đúng.

### Câu 28. Tích hợp Neo4j và RAG trong trợ lý diabetes

**Trả lời:** Em dùng Neo4j như lớp tổ chức và lọc bằng chứng có nguồn, kết hợp khả năng xếp hạng văn bản/embedding. Câu hỏi được ánh xạ tới topic; graph trả ID evidence đúng release; retriever đối chiếu với corpus kiểm checksum, chấm điểm và rerank. Evidence được gửi cho Education, sau đó kiểm claim/quote/nguồn rồi qua Safety.

Một câu hỏi triệu chứng sẽ tìm topic symptoms và đoạn liên quan; nó không cần gọi model Pima nếu không có assessment. Khi trả lời, hệ thống có thể cho thấy đoạn nào được dùng và URL nguồn nào hỗ trợ. Assertion graph dùng để xem quan hệ miền và provenance; không phải mọi câu trả lời đều đi qua một chuỗi assertion suy luận.

**Demo:** Mở mục Đồ thị tri thức, lọc `HAS_SYMPTOM`; tiếp theo hỏi về triệu chứng trong Knowledge assistant và đối chiếu evidence ID/citation. Có thể POST `/api/v2/knowledge/search` với `strategy` là `graph` hoặc `hybrid` để quan sát khác biệt. Khóa câu Cypher do code quy định, không cho LLM chạy Cypher tùy ý.

## IV. Intelligent Agent và Multi-Agent Systems — câu 29–38

### Câu 29. Intelligent Agent: môi trường, nhận thức, trạng thái, hành động và mục tiêu

**Trả lời:** Agent là một thực thể phần mềm nhận thông tin từ môi trường, duy trì biểu diễn trạng thái và chọn hành động nhằm đạt mục tiêu trong giới hạn được giao. Environment là nơi agent tương tác; perception là thông tin nhận được; state tóm tắt điều đã biết; action là việc có thể làm; goal định hướng đánh giá thành công; decision mechanism ánh xạ trạng thái thành hành động.

**Liên hệ:** Knowledge Agent nhận câu hỏi, topic và số lượt; mục tiêu là lấy evidence phù hợp; hành động là truy hồi qua các tool được phép. RL Agent chọn hành động giáo dục từ prediction/evidence và context mô phỏng. Safety quan sát input/output và chọn allow/block/clarification theo luật.

Không phải agent nào cũng cần LLM hoặc tự học online. Tính tự chủ phải được hiểu trong phạm vi policy và quyền tool, không phải tự do làm mọi thứ. Trong project, Coordinator quyết định luồng, các agent có quyền hạn và schema riêng.

### Câu 30. Kiến trúc tổng quát của một Intelligent Agent

**Trả lời:** Một agent thường có các khối nhận input → kiểm hợp lệ/quan sát → cập nhật state → truy cập knowledge hoặc model → ra quyết định → thực thi action/tool → trả output và nhận feedback. Knowledge chứa thông tin/tri thức; decision mechanism quyết định dùng thông tin đó như thế nào. Output nên nêu kết quả, trạng thái và lỗi thay vì luôn báo thành công.

**Ví dụ Knowledge Agent:** input là task chứa question/query/attempt; knowledge là corpus và Neo4j; cơ chế quyết định là routing topic, scoring, threshold và reranking; tool là đọc graph, encoder và snapshot; output gồm evidence, coverage, adequate, retrieval_method. Thiếu Neo4j có thể trả unavailable; evidence yếu được Coordinator xem xét truy hồi lại hoặc hỏi rõ.

**Chốt:** Kiến trúc agent không chỉ có prompt. Em phải chỉ ra state, decision policy, tool permission, contract và hành vi khi lỗi. Định nghĩa agent thực nằm trong `backend/app/research/agents.py`, schema trong `research/schemas.py`.

### Câu 31. Single-agent và MAS khác nhau thế nào?

**Trả lời:** Single-agent để một tác tử chịu trách nhiệm chính cho quá trình giải quyết; MAS phân trách nhiệm cho nhiều tác tử phối hợp qua giao tiếp và điều phối. Single-agent vẫn có thể gọi nhiều tool, vì thế nhiều tool không tự tạo thành MAS. MAS hữu ích khi cần chuyên trách, kiểm chứng chéo, phân quyền hoặc phối hợp công việc có yêu cầu khác nhau.

Trong project, Prediction phụ trách model, Knowledge phụ trách evidence, Education soạn, Verifier kiểm hỗ trợ, Safety kiểm phạm vi. Tách vai trò giúp theo dõi agent nào lỗi và áp quyền veto độc lập, nhưng thêm overhead, nguy cơ bất nhất và chi phí điều phối.

**Bằng chứng:** Đối chứng offline cùng budget hiện có completion **0.863636 ở cả MAS lẫn workflow trực tiếp**, mỗi phương pháp 44 runs. Mean latency snapshot MAS khoảng 1768 ms, workflow khoảng 1304 ms. Vì vậy em chọn MAS vì khả năng tổ chức và kiểm soát, chưa chứng minh MAS luôn chính xác hơn hoặc nhanh hơn. Baseline đối chứng trong code là direct workflow cùng tool, không nên tùy tiện gọi nó là một LLM agent tự chủ.

### Câu 32. Kiến trúc MAS: vai trò, giao tiếp, phối hợp và phân công

**Trả lời:** MAS cần xác định tác tử nào làm gì, input/output, cách giao tiếp, policy chọn việc, cách tổng hợp kết quả và xử lý bất đồng. Trong project, Coordinator là bộ điều phối tập trung: nhận run, gọi Safety đầu vào, gọi các agent cần thiết, nhận kết quả, quản lý retry và kiểm Safety đầu ra trước trả response.

Prediction không được gọi nếu chỉ có câu hỏi; Knowledge chạy khi cần evidence; RL chọn bước giáo dục; Education tạo candidate; Verifier có thể bác candidate; Safety có quyền chặn. Nếu evidence yếu, Coordinator có thể giao Knowledge truy hồi lại; bản nháp chưa được hỗ trợ có thể sửa trong ngân sách.

Giao tiếp bằng message có kiểu và `run_id` để tương quan, không phải các agent chat không giới hạn. Có tối đa hai lượt retrieval, hai draft và bốn provider attempts. Phân công theo nhiệm vụ chuyên biệt, không phải các agent bác sĩ chuyên khoa có quyền khám chữa bệnh.

### Câu 33. MAS tập trung, phi tập trung và phân cấp

| Kiểu | Điều phối | Ưu điểm | Hạn chế |
|---|---|---|---|
| Tập trung | Một Coordinator chính | Dễ quản lý policy, trạng thái và trace | Nút thắt, điểm lỗi trung tâm nếu không dự phòng |
| Phi tập trung | Agent tự phối hợp/đàm phán | Giảm phụ thuộc một bộ điều phối | Khó đồng thuận, xử lý xung đột và chứng minh safety |
| Phân cấp | Nhiều tầng quản lý/nhóm agent | Phân rã bài toán lớn, có phạm vi trách nhiệm | Phức tạp tầng điều khiển, lỗi truyền thông và phân quyền |

**Trả lời:** Project của em thuộc loại **điều phối tập trung**. Em ưu tiên kiểm soát luồng, retry, Safety và truy vết trong demo nghiên cứu. Tên “multi-agent” mô tả vai trò và tương tác, không có nghĩa đã triển khai nhiều máy hoặc nhiều process.

Nếu mở rộng, em có thể chia retrieval/prediction thành service độc lập và bổ sung hàng đợi, nhưng phải định nghĩa idempotency, timeout và version contract. Đó là hướng phát triển, chưa phải hạ tầng phân tán đã được kiểm chứng.

### Câu 34. Agent giao tiếp và trao đổi thông tin như thế nào?

**Trả lời:** Các cách thường dùng gồm message trực tiếp, shared blackboard/state, event bus và giao nhiệm vụ qua Coordinator. Message cần người gửi/nhận, loại nhiệm vụ, payload có schema, ID tương quan và trạng thái. Shared knowledge giúp nhiều agent dùng cùng nguồn nhưng phải kiểm version và quyền đọc/ghi.

**Liên hệ:** Message runtime chứa run/message ID, recipient và task đúng kiểu. Agent trả Result có agent_id/status/output/errors. Coordinator cập nhật state của riêng run và ghi Event gồm sequence, attempt, duration, reason. Evidence truyền kèm ID/URL/version/excerpt, không chỉ một câu tóm tắt không truy nguyên được.

Ví dụ Knowledge trả evidence, Coordinator đưa evidence đó cùng câu hỏi cho Education và Verifier. PostgreSQL lưu snapshot/trace để đọc lại sau thực thi, không phải một message broker. Project không triển khai giao thức FIPA/ACL đầy đủ; không nói đã dùng giao thức đó chỉ vì có message.

### Câu 35. Reinforcement Learning và cách agent học qua tương tác

**Trả lời:** RL học policy bằng cách tương tác với môi trường. Tại thời điểm `t`, agent ở state `s_t`, chọn action `a_t`, nhận reward `r_(t+1)` và state mới. Mục tiêu là tối đa hóa kỳ vọng tổng thưởng chiết khấu `G_t = Σₖ γᵏ r_(t+k+1)`. Policy `π(a|s)` quy định cách chọn hành động; reward đánh giá tín hiệu mục tiêu, không nhất thiết là nhãn đúng/sai cho mỗi bước.

Q-learning cập nhật:

`Q(s,a) ← Q(s,a) + α[r + γ max_a' Q(s',a') − Q(s,a)]`.

Với trạng thái kết thúc trong môi trường finite horizon của project, target chỉ còn `r`. Epsilon-greedy cân bằng khám phá và khai thác.

**Liên hệ:** Em train bảng Q trên môi trường **giáo dục mô phỏng**, 3 seeds × 8.000 episodes. Runtime chỉ đọc policy đóng băng hoặc dùng fallback khai báo rõ; không tự học trên người dùng và không chọn thuốc/liều điều trị. Reward mô phỏng không đại diện cải thiện sức khỏe thực.

### Câu 36. Markov Decision Process

**Trả lời:** MDP thường được mô tả bởi `(S,A,P,R,γ)`: tập state, tập action, xác suất chuyển trạng thái, hàm reward và hệ số chiết khấu. Policy là chiến lược chọn action trên MDP. Tính Markov nghĩa là với state hiện tại đủ thông tin, phân phối bước tiếp theo không cần phụ thuộc thêm toàn lịch sử.

**Liên hệ cụ thể:** State có prediction_band, knowledge, engagement, evidence, safety, previous_action và remaining_budget. Kích thước `(3,3,3,3,2,7,7)` tương ứng **7.938 trạng thái**. Action gồm giải thích giới hạn dự đoán, giáo dục chung, hiển thị evidence, hỏi hiểu biết, yêu cầu làm rõ và gợi ý trao đổi chuyên gia.

Previous_action giúp biểu diễn phạt lặp; remaining_budget làm rõ chân trời hữu hạn. Transition và reward là giả định mô phỏng, không ước lượng từ hành trình bệnh nhân. Runtime knowledge/engagement dùng giá trị mô phỏng có nhãn, không phải đo hiểu biết thực. Các mask hạn chế action theo evidence/safety và Safety gate vẫn có thể veto hành động.

### Câu 37. AI agent khác một component phần mềm truyền thống ở đâu?

**Trả lời:** Component truyền thống thường thực hiện một thao tác theo interface đã định. Agent được thiết kế quanh mục tiêu, quan sát/state và policy lựa chọn hành động, có thể chọn tool hoặc phối hợp với agent khác. Tuy nhiên ranh giới không tuyệt đối: agent cũng được xây từ component, còn component có thể chứa logic quyết định phức tạp.

Không thể chỉ đổi tên hàm thành “Agent” là chứng minh có tính tự chủ. Em cần chỉ ra điều kiện ra quyết định, các lựa chọn có thể xảy ra, feedback và quyền hạn. Ví dụ RL chọn hành động trong tập cho phép; Knowledge có thể trả evidence đủ hoặc yếu; Verifier có thể reject khiến Coordinator sửa bản nháp.

**Tự nhận đúng phạm vi:** Prediction Agent chủ yếu bọc model service cùng contract/persistence; tính thích ứng của toàn hệ nằm ở routing và các quyết định phối hợp. Các vai trò có mức tự chủ khác nhau, không phải sáu LLM độc lập cùng suy nghĩ tự do.

### Câu 38. Thách thức phát triển MAS

**Trả lời:** Em nhóm thành sáu vấn đề: phân công trùng/thiếu việc; truyền thông và contract lệch; xung đột quyết định; lỗi/timeout dây chuyền; quyền tool và dữ liệu nhạy cảm; đánh giá chi phí–chất lượng.

Project xử lý bằng typed tasks, trạng thái theo run, timeout và ngân sách retry, source admission, artifact version/checksum, trace có tương quan và Safety fail-closed. Education không được tự duyệt claim của mình; khi Verifier bác hoặc Safety chặn, Coordinator không được bỏ qua chỉ vì muốn hoàn thành tác vụ.

Prompt injection có thể tới từ câu hỏi hoặc tài liệu, nên tài liệu phải được coi là dữ liệu, không là lệnh cấp quyền. Cần kiểm cả đầu vào lẫn đầu ra và không cho chạy tool tùy ý. Thử nghiệm lỗi dependency, artifact sai và nội dung nguy hiểm là kiểm tra kỹ thuật; số ca qua test không chứng minh toàn bộ rủi ro ngữ nghĩa đã được loại bỏ.

**Chốt:** Thêm agent có thể tăng latency và tạo lỗi mới; phải có ablation/baseline cùng điều kiện, không chỉ demo một câu thành công.

## V. Ứng dụng thực tế và Project Diabetes MAS — câu 39–51

### Câu 39. Giải thích ứng dụng dự đoán diabetes của em

**Trả lời:** Trong project MAS, em dùng dataset Pima có 768 dòng, tám đặc trưng số và nhãn Outcome nhị phân; 500 nhãn âm, 268 nhãn dương. Tám đặc trưng theo thứ tự là pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree và age. Metadata gốc mô tả cohort phụ nữ Pima từ 21 tuổi trở lên; tập hẹp này không đại diện mọi người dùng.

Preprocessing thay 0 bằng missing ở glucose, blood_pressure, skin_thickness, insulin và bmi, sau đó median imputation và standardization fit trên train. Pregnancy=0 vẫn hợp lệ.

Mạng PyTorch MLP **8→32→16→1**, ReLU, dropout 0.15; BCEWithLogitsLoss và Adam. Output là score sigmoid và lớp theo ngưỡng cố định 0.5, kèm version và cảnh báo. Test accuracy khoảng 75.86%, ROC-AUC khoảng 0.8634; recall khoảng 53.66%, nên không dùng làm chẩn đoán.

**Điểm cần nói rõ:** Dataset huấn luyện lịch sử không phải dữ liệu synthetic. Chỉ mẫu nhập và hồ sơ demo mới được đánh dấu SYNTHETIC. Bài CNN cũ là một artifact khác, không phải checkpoint đang phục vụ trong MAS.

### Câu 40. Phát triển và triển khai ứng dụng diabetes

**Trả lời:** Em tách huấn luyện offline và serving. Offline tạo split, fit preprocessing, train/chọn checkpoint, đo test và xuất manifest/checksum. Serving không train lại mà nạp artifact tin cậy, kiểm version/feature/checksum và chạy inference.

Frontend React/Vite có form tám trường và xác nhận synthetic. Request đi tới FastAPI, kiểm schema rồi Coordinator gọi Prediction Agent khi phù hợp. Prediction service áp preprocessing đã fit, nạp MLP, chạy CPU inference, trả score/class/warnings; PostgreSQL lưu prediction/run và trace. Knowledge/Education có thể giải thích giới hạn và kiến thức chung bằng nguồn.

**Demo native:** `python scripts/start_final_demo.py start`; web `http://127.0.0.1:8082`, user `demo`, mật khẩu trong `.env.demo`. Lệnh status để kiểm trạng thái thực. Gateway có đăng nhập; không phải hệ tài khoản nhiều người dùng hoàn chỉnh. Docker đã có cấu hình nhưng runtime Docker/cloud độc lập chưa được xác minh trong đợt bàn giao trước; native chạy không được gọi là đã deploy production/cloud.

### Câu 41. So sánh diabetes, stock và house-price application của em

| Nội dung | Diabetes trong MAS | Stock Assignment_06 | House price |
|---|---|---|---|
| Input | 8 đặc trưng Pima | 30 phiên OHLCV của AAPL | Diện tích, mặt tiền, đường, tầng, phòng; một số bản có hướng/pháp lý/thành phố |
| Đích | Outcome 0/1 | Close phiên kế tiếp | Price |
| Cấu trúc | Bảng, một dòng/mẫu | Chuỗi có thứ tự | Bảng số + phân loại |
| Model được đối chiếu | Frozen MLP | PyTorch/Keras RNN | A02 chọn Random Forest; A04 có Conv1D thử nghiệm riêng |
| Output | Score/lớp có cảnh báo | Giá dự báo | Giá dự báo |
| Metric | Precision/recall/F1/AUC | MAE/RMSE/R², so persistence | MAE/RMSE/R² |

**Trả lời:** Điểm chung là giữ preprocessing giống train và tách đánh giá khỏi lựa chọn model. Điểm khác là stock phải bảo vệ thứ tự thời gian và kiểm naive baseline; diabetes cần kiểm class imbalance và sai âm; giá nhà cần xử lý khác biệt vị trí/đặc trưng và phân phối giá.

Không khẳng định cả ba bản đang phục vụ đều là DL: config A02 house hiện chọn Random Forest. Bản CNN nằm ở Assignment_04 là thực nghiệm riêng. Chỉ diabetes đã được ghép vào MAS đang bảo vệ.

### Câu 42. Demo một input mới từ giao diện tới output

**Trả lời kèm thao tác:** Em mở Assessment, bấm điền mẫu rồi xác nhận **SYNTHETIC**. Mẫu minh họa:

```json
{
  "pregnancies": 0, "glucose": 100, "blood_pressure": 70,
  "skin_thickness": 20, "insulin": 50, "bmi": 22,
  "diabetes_pedigree": 0.3, "age": 30
}
```

Frontend kiểm dữ liệu, POST `/api/v2/mas/runs` với assessment và `is_synthetic: true`. Backend kiểm schema; Safety xét đầu vào; Prediction Agent xác nhận feature/order và artifact; imputer/scaler transform; MLP forward → sigmoid → score và class. Các agent còn lại xử lý phần giáo dục khi có nhiệm vụ tương ứng. Sau kiểm chứng/Safety, run được lưu và trả về UI.

Em đọc **score thực đang hiển thị**, không học thuộc một số tự đặt. Sau đó mở Hành trình agent, xem model_version, status và run_id, tải lại run để chứng minh persistence. Nếu thiếu artifact hoặc dependency, phải trình bày unavailable/degraded thực, không thay bằng score mẫu.

### Câu 43. Kiến trúc tổng thể và lý do chọn MAS

**Trả lời:** Kiến trúc gồm UI React/Vite → FastAPI → Coordinator → các agent/tool → kiểm chứng và Safety → PostgreSQL/response. Prediction dùng MLP; Knowledge dùng corpus/Neo4j/embedding/reranker; RL dùng Q-policy; Education và semantic review gọi provider; Safety dùng luật xác định.

```text
UI → API → Coordinator → Safety đầu vào
                     → Prediction nếu có assessment
                     → Knowledge → RL → Education → Verifier
                     → kiểm nguồn + Safety đầu ra → lưu run/trace → UI
```

Sơ đồ là luồng khái quát; có nhánh skip, clarification, fallback và retry có giới hạn. Coordinator là điều phối, còn sáu agent nghiệp vụ có contract riêng.

Em chọn MAS để tách quyền và trách nhiệm, kiểm độc lập, quan sát lỗi và thay tool mà không trộn toàn bộ logic vào một prompt. Chi phí là tăng orchestration/latency. Kết quả đối chứng chưa chứng minh ưu thế completion so workflow trực tiếp; lý do thiết kế cần được phân biệt với kết luận thực nghiệm.

### Câu 44. Từng agent: trách nhiệm, input, output và tương tác

| Vai trò | Input | Output/quyết định | Tương tác |
|---|---|---|---|
| Coordinator | RunInput | Phân công, state, response/trace | Quản lý toàn luồng và ngân sách |
| Prediction | Assessment synthetic | PredictionResult: score/class/version/warnings | Cung cấp kết quả model cho bước sau |
| Knowledge | Question, query, attempt | Evidence, coverage, adequate, method | Gửi evidence cho Coordinator |
| RL | Prediction/evidence | Action, policy_version, decision_source | Định hướng bước giáo dục |
| Education | Question, language, evidence, action, feedback | Claim có supports hoặc fallback trích nguồn | Soạn candidate để Verifier kiểm |
| Verifier | Question, candidate, evidence | Verdict, reason, candidate digest | Có thể bác để sửa/abstain |
| Safety | Input/output, action/provenance | Allow/warning/block/clarification/escalation theo policy | Veto trước công bố |

**Trả lời:** Có **sáu agent nghiệp vụ cộng Coordinator**, không đếm nhầm thành sáu vai trò tổng cộng. Tool, timeout và fallback được khai báo trong `research/agents.py`. Prediction không train; Knowledge không nhận URL/Cypher tùy ý; Education không tự duyệt nội dung; Safety không bị LLM ghi đè. Agent không được gọi trong một nhánh có thể mang trạng thái skipped, không giả output cho đủ bảng.

### Câu 45. Tích hợp model DL vào MAS

**Trả lời:** Prediction Agent là đầu mối gọi model service. Coordinator chỉ giao task khi run có assessment hợp lệ và xác nhận synthetic. Service kiểm manifest, feature schema và checksum, nạp checkpoint cùng preprocessing đã fit, đặt model ở eval, chạy inference rồi trả PredictionResult có version.

Coordinator nhận output có kiểu, chuyển phần cần thiết cho RL/Education và giữ cảnh báo. Kết quả model không tự có quyền chẩn đoán hay bỏ qua Safety. Persistence của prediction dùng repository/transaction; nếu inference hoặc ghi prediction lỗi, luồng không được báo thành công giả.

**Code để mở:** `backend/app/research/agents.py` → `PredictionAgent`, `backend/app/mas/agents/` và `backend/app/ml/serving.py`. Model không được gọi trực tiếp từ JavaScript, không gửi weight cho trình duyệt. Lazy load có khóa tránh mỗi request nạp lại toàn bộ; state của run vẫn tách riêng. Artifact hỏng trả unavailable thay vì âm thầm chuyển sang model khác.

### Câu 46. KG/Neo4j đã triển khai và Cypher thực

**Trả lời:** KB hiện có 14 nguồn NIDDK, 449 evidence và 11 assertion được tuyển chọn có quote hỗ trợ. Schema gồm Source, Evidence, Topic, Concept và Assertion theo namespace Diabetes. Các quan hệ miền là HAS_RISK_FACTOR, HAS_SYMPTOM, SCREENED_WITH, HAS_COMPLICATION; HAS_CHUNK/SUPPORTED_BY/SUBJECT_OF/OBJECT giữ nguồn và cấu trúc assertion.

Truy vấn mẫu tương ứng logic runtime, truyền `$release` bằng checksum corpus hiện hành:

```cypher
MATCH (a:DiabetesAssertion {release:$release})
  -[:SUPPORTED_BY]->(c:DiabetesEvidence)
RETURN a.subject AS subject, a.predicate AS predicate,
       a.object AS object, a.supporting_quote AS quote,
       c.id AS evidence_id, c.url AS source_url
ORDER BY a.id LIMIT 100;
```

**Demo:** Mở web Đồ thị tri thức hoặc Neo4j Browser và `kb_diabetes_queries.cypher`. Tệp bàn giao `kb_diabetes.cypher` xuất từ corpus kiểm checksum, có manifest; kiểm import DML hai lần và readback thực đã PASS ngày 06/11, transaction rollback. Không nói đó là kiểm import constraint trên một DB trống; phần đó chưa được verifier thực hiện. KB không chứa hồ sơ bệnh nhân thật.

### Câu 47. RAG tích hợp thế nào và giảm hallucination ra sao?

**Trả lời:** Knowledge Agent route topic, lấy evidence ID từ Neo4j đúng release, kết hợp TF-IDF và multilingual MiniLM, rồi cross-encoder rerank ở hybrid. Mặc định chọn tối đa ba evidence; API search cho phép k từ 1 đến 5. Education sinh claim nguyên tử có evidence ID/quote và metadata provider thực.

Verifier đối chiếu metadata với corpus, quote chính xác, số liệu/rendering và digest candidate; có lượt semantic review riêng. Coordinator lặp lại kiểm nguồn xác định, sau đó Safety đầu ra. Evidence yếu có tối đa hai retrieval attempts; draft chưa đạt được sửa trong tối đa hai lượt; tổng provider attempts tối đa bốn. Hết ngân sách thì fallback/clarification/withheld theo policy.

Nguồn allowlist, snapshot/checksum, domain routing và quyền tool hẹp giảm rủi ro. Nhưng reviewer cùng provider chưa độc lập về lỗi mô hình; quote đúng chưa đủ bảo đảm diễn giải đúng. Kết quả “verified” là qua kiểm tự động trong phạm vi protocol, không phải bác sĩ đã xác nhận chính xác lâm sàng.

### Câu 48. Luồng đầy đủ khi người dùng hỏi về diabetes

**Trả lời:** Với câu hỏi kiến thức không kèm assessment, luồng khái quát là:

1. API kiểm RunInput, tạo run/message correlation.
2. Coordinator gọi Safety đầu vào; nếu bị chặn thì dừng nhánh nội dung.
3. Prediction **skip** vì không có tám đặc trưng; không tự đoán feature.
4. Knowledge route và retrieve evidence; có thể retrieve lại nếu yếu trong budget.
5. RL chọn hành động giáo dục phù hợp với prediction/evidence và context có nhãn.
6. Education tạo candidate từ evidence hoặc fallback có nhãn.
7. Verifier kiểm hỗ trợ; có thể feedback/sửa trong budget hoặc bác.
8. Coordinator kiểm nguồn và Safety đầu ra, lưu response/trace vào PostgreSQL và trả UI.

Nếu có assessment synthetic hợp lệ, thêm Prediction và truyền score/warnings cho các bước sau. Luồng lỗi/clarification có thể kết thúc sớm; không giả định mọi request đều chạy thành công cả sáu agent. Run và trace cho phép giải thích nhánh thực đã xảy ra.

### Câu 49. Demo MAS trên laptop với một tình huống

**Kịch bản trả lời và thao tác khoảng 2–3 phút:**

1. Chạy `python scripts/start_final_demo.py status`; nếu chưa chạy, dùng `start`. Mở web 8082, đăng nhập `demo` bằng mật khẩu local.
2. Mở Đồ thị tri thức, lọc `HAS_SYMPTOM`, mở passage/URL để chứng minh KB có bằng chứng thật.
3. Hỏi “Bệnh tiểu đường có những triệu chứng nào?”. Nói rõ đây là tìm hiểu kiến thức chung, không yêu cầu tự chẩn đoán.
4. Đọc response thực và nhãn generation_mode; mở nguồn. Nếu LLM lỗi nhưng có trích nguồn, nói rõ extractive fallback. Nếu hỏi rõ hoặc unavailable, trình bày nguyên nhân thực.
5. Mở Hành trình agent, chỉ Knowledge, Education, Verifier, Safety và Prediction skipped; tải run để thấy trace đã lưu.
6. Nếu còn thời gian, thử “Should I increase my insulin dose?” để cho thấy Safety veto; không đưa câu trả lời điều chỉnh liều.

**Nhánh DL bổ sung:** Dùng mẫu SYNTHETIC ở câu 42, chỉ ra score/version thực. Trước thi cần thử lại dependency và provider; link localhost chỉ truy cập được khi dịch vụ đang chạy, không khẳng định demo đang hoạt động chỉ dựa tài liệu cũ.

### Câu 50. Đánh giá MAS như thế nào?

**Trả lời:** Em đánh giá từng thành phần và toàn luồng, với baseline, split, dataset version và chi phí rõ ràng.

| Tầng | Chỉ số/kiểm tra | Kết quả lưu đáng nhớ |
|---|---|---|
| DL | Accuracy, P/R/F1, ROC-AUC, AP, calibration | MLP accuracy 0.758621; recall 0.536585; ROC-AUC 0.863415 |
| Baseline DL | Cùng split/preprocess | LR accuracy 0.775862 cao hơn MLP trên split này |
| Retrieval | Recall@k, precision kết quả trả, MRR, provenance, latency | Hybrid confirmatory: Recall@3 0.290972, precision 0.570833, MRR@3 0.625 |
| Response | Evidence relevance, claim support, coverage LLM/fallback | Workflow 6 câu: 6/6 có evidence đúng mục; 4/6 LLM được nhận qua kiểm tự động |
| Coordination | Completion, retry/budget, branch/trace, lỗi | MAS và direct workflow đều completion 0.863636; 44 runs mỗi cách, provider disabled |
| Latency | End-to-end và từng stage | Offline snapshot mean: direct 1303.84 ms; MAS 1768.23 ms |
| Reliability | Dependency outage, artifact hỏng, persistence, Safety veto | Đợt V2: 216 backend PASS/43 SKIP; frontend 22 PASS; KB live/browser PASS |

Các metric retrieval trên thuộc corpus mở rộng và bộ confirmatory phrasing lưu trong `diabetes_rag.csv`, không trộn với Recall@5 trên corpus lịch sử. Precision là theo số kết quả thực trả, không cố định chia k khi trả ít hơn. Sáu workflow đã được xem trước, chưa phải blind test. Các test bị skip không được tính PASS. Chưa có human clinical accuracy hay p95 latency được xác lập từ những số mean này.

**Nguồn số liệu:** `docs/model_card.md`, `experiments/results/diabetes_rag.csv`, `final_mas.csv`, `final_workflows.csv`, `docs/validation/report_v2/`.

### Câu 51. Hạn chế, rủi ro và hướng cải thiện

**Trả lời:** Hạn chế quan trọng nhất là chưa có xác minh lâm sàng. MLP học trên cohort Pima hẹp, test nhỏ, recall còn thấp, score chưa hiệu chỉnh và chưa external validation. KB 14 nguồn tuy có provenance nhưng vẫn hẹp, chủ yếu tiếng Anh; routing paraphrase có thể bỏ sót. Retrieval đúng mục chưa đồng nghĩa claim đúng hoàn toàn; LLM và semantic reviewer có thể cùng sai.

RL chỉ học trên simulator và reward giả định; knowledge/engagement runtime không phải đo thật. MAS thêm overhead, chưa thắng direct workflow về completion trong control hiện có. Safety có thể chặn nhầm hoặc bỏ sót diễn đạt mới. Gateway login local chưa phải bảo mật production; Docker/cloud vận hành độc lập chưa kiểm chứng đầy đủ.

**Cải thiện theo thứ tự:** mở rộng bộ đánh giá có nhãn chuyên gia và tập ngoài; đo calibration/fairness và interval; tăng nguồn được rà soát/version, bổ sung tiếng Việt; đánh giá claim-level và reviewer độc lập; thêm adversarial/failure cases và đo p50/p95/cost; rồi hoàn thiện auth, phân quyền, monitoring, backup, container và triển khai. Mọi thay đổi ngưỡng/model phải chọn trên train/validation và đo lại, không sửa theo test để lấy số đẹp.

**Chốt vấn đáp:** Em bảo vệ phần đã làm bằng code, artifact và trace; những cải tiến này là kế hoạch, không tính thành chức năng đã triển khai.

## Phiếu nhớ nhanh trước khi thi

- **MLP:** 8→32→16→1; seed 42; split 537/115/116; BCEWithLogitsLoss; Adam 0.001; batch 32; dropout 0.15; tốt nhất epoch 24, chạy 44 epochs.
- **Kết quả:** accuracy 75.86%; precision 70.97%; recall 53.66%; F1 61.11%; ROC-AUC 0.8634; TP/TN/FP/FN = 22/66/9/19. LR accuracy tốt hơn MLP trên split này.
- **KB:** 14 nguồn, 449 đoạn, 11 assertion; NIDDK; có quote, URL, release và checksum.
- **Retrieval:** TF-IDF + multilingual MiniLM 384 chiều + Neo4j candidates + cross-encoder; vector matrix local, không phải Neo4j vector index.
- **MAS:** sáu agent nghiệp vụ và Coordinator tập trung; tối đa 2 retrieval, 2 draft, 4 provider attempts; Safety hai đầu và fail-closed.
- **RL:** Q-table, simulator, 7.938 states, sáu action giáo dục; không điều trị, không online learning.
- **Control:** MAS/direct cùng completion 0.863636; không tuyên bố MAS vượt baseline.
- **Phạm vi:** native demo; chưa đủ căn cứ production/clinical/cloud; dataset train không synthetic, mẫu demo là synthetic.

## Tài liệu để mở khi thầy hỏi code

Các đường dẫn dưới tính từ thư mục `diabetes-mas-final`:

| Cần chứng minh | Tệp/đường dẫn |
|---|---|
| Dữ liệu, split, preprocessing | `docs/data_card.md`, `experiments/results/phase02/` |
| Model và kết quả DL | `docs/model_card.md`, `backend/app/ml/serving.py` |
| Agent và tool/timeout | `backend/app/research/agents.py`, `research/schemas.py` |
| Điều phối | `backend/app/research/coordinator.py` |
| Corpus và graph | `backend/app/research/corpus.py`, `graph.py` |
| Retrieval/encoder/reranker | `backend/app/research/retrieval.py`, `semantic.py`, `reranker.py` |
| Grounding và Safety | `backend/app/research/grounding.py`, `safety.py` |
| RL/MDP | `docs/rl_mdp.md`, `backend/app/rl/` |
| Neo4j bàn giao/demo | `kb_diabetes.cypher`, `kb_diabetes_queries.cypher` |
| Đối chứng và workflow | `experiments/results/final_mas*`, `final_workflows*` |
| CNN cũ; chứng khoán | `../Assignment_04/`, `../Assignment_06/` |
| Hạn chế và version V2 | `docs/report_v2_readiness.md`, `docs/final_handoff.md` |

## Ghi chú nguồn và cách dùng tài liệu

Thứ tự và phạm vi câu hỏi lấy trực tiếp từ PDF của giảng viên. Số liệu cá nhân lấy từ các artifact local nêu ở từng câu; không phải số liệu từ website. Nguồn tham khảo ngoài được gắn ở đúng câu liên quan để đối chiếu khái niệm/API, không thay thế bằng chứng triển khai của em. Với các ví dụ y khoa, tài liệu chỉ trình bày cách biểu diễn/truy hồi kiến thức chung, không đưa hướng dẫn chẩn đoán hoặc điều trị cá nhân.

Học theo cụm ý và giải thích bằng lời của mình. Khi thầy yêu cầu số thực hoặc demo, mở artifact/run hiện tại; không học thuộc số output tự đặt và không gọi một kết quả fallback là LLM thành công.
