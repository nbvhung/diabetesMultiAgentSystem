# Demo giải thích 8 phút

| Phút | Nội dung | Bằng chứng |
|---|---|---|
| 0–1 | Bài toán, phạm vi giáo dục, Pima khác synthetic demo | Overview + data/model card |
| 1–2 | Kiến trúc sáu agent; centralized MAS trong một process | Sơ đồ + agent definitions |
| 2–3 | Assessment synthetic và question chung; chạy Coordinator | POST thật, score/model version/limitations |
| 3–4 | Evidence/claims, citation gốc, mode llm hoặc fallback | Link nguồn, quote, Verifier |
| 4–5 | Trace: dispatch, RL action, feedback, Safety gates, SQL readback | Monitor và run ID |
| 5–6 | Unsafe insulin → veto; weak evidence → clarification | Actual refusal, không fake citation |
| 6–7 | Prediction/RAG/MAS/RL/safety/LLM results | CSV/manifest, baseline và mẫu số |
| 7–8 | Test/deployment và hạn chế; trả lời phản biện | 249/22/6 checks, HTTPS tạm, Docker BLOCKED |

Missing Neo4j được trình bày bằng fault scenario đã lưu hoặc test service riêng, không tắt DB chính thiếu kiểm soát. Ghi “explicit fault injection”, phân biệt với lỗi hệ thống thực sự tự xảy ra. Timeout/provenance tampering là synthetic software probes, không phải thử nghiệm trên bệnh nhân.

Câu kết luận phù hợp: “Hệ thống chứng minh luồng phối hợp và các biên kiểm soát chạy được. Chúng tôi không chứng minh MAS luôn tốt hơn; ưu tiên tiếp theo là matched-budget evaluation, expert answer review và đóng gate Docker.” Chỉ đổi readiness khi có log Docker thực tế mới.
