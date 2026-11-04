# Thiết kế agent hiện hành

Diabetes MAS là **MAS điều phối tập trung trong một modular monolith**, không phải sáu microservice hoặc sáu LLM độc lập. Từng agent có mục tiêu hữu hạn, typed task/result, quyền tool, timeout và quyền từ chối riêng. Coordinator chọn agent theo trạng thái, nhận feedback, retry trong ngân sách và lưu quyết định. Số lượng agent không tự chứng minh lợi ích khoa học.

| Agent | Mục tiêu / phản ứng | Tool | Timeout |
|---|---|---|---:|
| Prediction | Score/class khi có assessment hợp lệ; thiếu model → unavailable | Frozen PyTorch, train-only preprocessing, prediction INSERT | 30s |
| Knowledge | Evidence có provenance; evidence yếu → feedback để retrieve lại | Neo4j read, local encoder/reranker, corpus snapshot | 20s |
| RL Decision | Chọn next educational action; thiếu/corrupt policy → fallback có nhãn | Numeric Q-policy, action whitelist | 3s |
| Education | Claims chỉ từ evidence; provider lỗi → exact-source fallback | Groq structured composition | 30s |
| Verifier | Bác claim sai quote/number/source hoặc không được hỗ trợ | Snapshot admission, separate semantic-review call | 30s |
| Safety | Bảo vệ cả đầu vào và công bố; có quyền veto không thể bị LLM bỏ qua | Deterministic diabetes safety rules | 2s |

Nguồn: `backend/app/research/agents.py`. Một provider được chia sẻ có budget per-run; Verifier là agent/role/call khác, **không phải một foundation model khác**. Lỗi tương quan vẫn có thể xảy ra.

`Message` gắn UUID run/message và recipient khớp task; `Result` bắt output/status/agent khớp; `Event` có sequence, reason, duration, attempt và redacted summaries. Coordinator tạo registry và mutable run state riêng; shared inference services dùng khóa và read-only weights. Không để câu hỏi hoặc rejected draft vào summary của trace. Events persisted dùng JSON versioned; không thay nhãn snapshot v1 thành v2.

Ngân sách: tối đa hai retrieval rounds, hai draft attempts, bốn provider attempts; deadline 85 giây sau warmup. Task timeout dùng asyncio; không nên diễn giải thành khả năng kill mọi blocking native call. Warmup tải CPU model trước mở transaction/budget; requests không download weights.

Luồng phản hồi: insufficient evidence → query rewrite trong lượt 2; rejected candidate → reason-only feedback rồi compose lại; hết budget → exact quotes được kiểm lại hoặc clarification; Safety failure → fail closed. SQL commit là điều kiện trả 201; SQL lỗi không trả “đã lưu”. [Sequence](report/figures/sequence.png), [contracts](agent_contracts.md), [actual trace](validation/phase08/public_demo.json).

Đây là sự tự chủ bị giới hạn bởi policy và controller; không có tự mở quyền tool, persistent conversation, online learning hay negotiation tự do. Phân rã agent giúp tách trách nhiệm và audit, nhưng benchmark hiện chưa chứng minh bản thân phân rã làm tăng chất lượng so với một direct workflow có cùng ngân sách.
