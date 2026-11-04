# Dàn ý 12 slide

1. **Tên đề tài và phạm vi:** hệ đa agent cho diabetes; Nguyễn Bá Việt Hùng, nhóm 13/lớp 06; giáo dục, không chẩn đoán.
2. **Vấn đề:** classifier không giải thích; LLM có thể sai; cần evidence, kiểm chứng và fail-closed.
3. **Yêu cầu và kết quả audit:** DL + DB + Neo4j/KB/RAG + agents + rules + RL; phần nào đã chạy, Docker còn thiếu engine.
4. **Kiến trúc:** dùng `report/figures/architecture.png`; frontend, Coordinator, sáu agents, PostgreSQL/Neo4j.
5. **Agent contracts và autonomy:** trách nhiệm, task/result, tool rights; không phải sáu LLM hoặc sáu microservice.
6. **Deep Learning:** Pima/split/preprocessing, MLP/baselines, FN=19/41; dùng `prediction_evaluation.png`.
7. **KG/RAG/LLM:** 14 nguồn/449 chunks/11 assertions; provenance và exact quotes; Groq inference, không train LLM.
8. **RL vs rules:** state/action/reward; simulator; Q reward 4.276 vs rules 4.311; Safety veto ưu tiên hơn Q-value.
9. **Demo 2 phút:** theo script, không chiếu env; actual citations và refused insulin.
10. **Trace và feedback:** dùng `actual_trace.png`; evidence yếu, retry, verifier repair và hai gates.
11. **Evaluation:** các bảng trong report; MAS budget confound, LLM 3/6 coverage và 3/3 conditional acceptance; không dùng 100% accuracy.
12. **Verification, limitations và kết luận:** 249 backend/22 frontend/6 browser PASS; HTTPS temporary verified; cloud NOT_COMPLETED, Docker runtime BLOCKED; kế hoạch đóng gate.

Mỗi slide có source caption; số liệu lấy từ bundle và giữ scope. Không biến dàn ý thành tuyên bố đã có file PowerPoint; tài liệu này là outline để thiết kế slide, không phải slide deck đã render.
