# Bản chốt để chạy demo và viết báo cáo tổng hợp

Đây là hướng dẫn bản native cuối, kế tiếp snapshot Phase 08. Số liệu mới nằm ở `experiments/results/final_mas*` và `final_workflows*`; không thay tên/ghi đè các experiment lịch sử. [Đọc bài tham khảo và quyết định áp dụng](reference_final_review.md).

## Chạy và dừng

Với môi trường và `.env` đã cấu hình trên máy hiện tại:

```powershell
python scripts/start_final_demo.py start
python scripts/start_final_demo.py status
python scripts/start_final_demo.py stop
```

Web: **http://127.0.0.1:8082**, username `demo`, password trong `.env.demo`. Lệnh start kiểm model/policy/corpus, migrate/seed idempotent, build frontend, tạo API riêng port 18082 và gateway. API 8000 của người dùng không bị thay thế; stop chỉ dừng các process demo được script kiểm tra quyền sở hữu. PostgreSQL phải đang chạy và các artifacts đáng tin phải có sẵn. Windows dùng local Neo4j manager có sẵn; Linux cần Neo4j đã khởi động theo installation.

Nếu muốn HTTPS tạm, dừng bản demo trước rồi start với `--tunnel`; đọc URL thực ở `status`. Không coi URL trong các tài liệu lịch sử là URL vĩnh viễn. Cần internet và cloudflared; không phải cloud hosting độc lập.

## Phần đã cải thiện

1. Routing nhận thêm cách hỏi tiếng Việt: “biểu hiện”, “dễ mắc”, “trì hoãn”, “hoạt động thể lực”, “ABCs”. Domain checks và Safety vẫn áp dụng.
2. Khi Groq từ chối JSON schema, Education thử lại một lần với yêu cầu một claim ngắn/quote chính xác. Giới hạn 4 provider attempts/run, timeout, source admission, Verifier và Safety giữ nguyên. Auth/rate-limit/missing evidence không được content-retry. Trace/warnings ghi `GROQ_SCHEMA_RETRY_RECOVERED` hoặc `...EXHAUSTED`; fallback vẫn có nhãn.
3. Đối chứng MAS mới cùng maximum budget. Baseline trực tiếp vẫn không dispatch agent/Coordinator. Kết quả hòa về completion/evidence ở phép đo offline là kết quả hợp lệ, không ép MAS thắng.
4. Hai experiment mới có CSV/JSON/PNG/manifest và được hiển thị qua experiment API kiểm checksum. Giao diện không dựng metric mặc định.
5. Một lệnh native và bộ bàn giao source/artifacts riêng; không mang secrets, DB dumps hoặc raw Pima vào source archive.

## Cách dùng số liệu khi viết

- Prediction/RL: giữ kết quả frozen và caveats trong model_card/rl_mdp. Không train thêm để thay số đẹp hơn; DL/RL không được chứng minh vượt mọi baseline.
- RAG lịch sử: các score cũ thuộc source/config/timestamp đã ghi. Alias router mới có regression riêng; không tự gắn score cũ thành phép đo mới.
- `final_mas.csv`: cùng 22 scenarios × 2 repeats mỗi phương pháp, provider disabled, paired/shuffled seed 42. Dùng cùng caps 2 retrieval/2 drafts/4 attempts; báo task completion, conditional evidence relevance, safety invariants và latency. Đây là offline architectural control; không đo chất lượng LLM hoặc sức khỏe.
- `final_workflows.csv` + rows: sáu câu vi/en đã được xem trước, qua Coordinator đầy đủ, genuine provider khi có `--live`, lưu SQL và GET readback. Dùng tất cả sáu trong mẫu số; tách `llm`, `extractive`, `clarification`. Verifier acceptance không phải medical accuracy. Các lần provider có thể dao động, không quy chênh lệch vài câu thành hiệu ứng thống kê của retry.
- Bản đo workflow trước sửa schema retry được giữ ở `experiments/results/final_release_snapshots/before_schema_retry`. Không so nó trực tiếp với benchmark LLM component-only lịch sử như hai phép đo cùng protocol.

Số liệu chốt, kết quả test, checksum và các gate còn lại: `docs/validation/final_release/release.json` và `release_summary.md`. Bộ 48 trang trước đó là snapshot; khi viết quyển tổng hợp, ưu tiên số liệu mới và phần bổ sung này, giữ nguyên phần lý thuyết/nguồn phù hợp. Không copy bài tham khảo làm kết quả của mình.

## Trạng thái bàn giao

Chốt trong phạm vi **native research/demo và nguyên liệu viết báo cáo** sau khi test/launcher thực thi thành công. Đây không phải clinical deployment. Docker files đã có nhưng Docker runtime trên host chưa được kiểm chứng; cloud hosting chưa hoàn thành. Không đổi gate Docker cũ thành PASS bằng kiểm thử native. Không cần thêm agent, CNN/RNN hoặc train foundation LLM để bắt đầu viết báo cáo tổng hợp.
