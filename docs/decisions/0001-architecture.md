# ADR 0001 — Modular monolith và Python state-machine

Trạng thái: chấp nhận cho Phase 00. Ngày: 2026-11-02.

Bối cảnh: đồ án cá nhân cần chứng minh phối hợp agent có contract, trách nhiệm và kiểm thử rõ, trong khi DL, DB, RAG, rules, RL là tools hỗ trợ. Distributed microservices làm tăng chi phí deploy, xử lý consistency và lỗi mạng mà chưa giúp đánh giá mục tiêu MAS.

Quyết định: modular monolith FastAPI với module MAS riêng; Pydantic v1.0 envelope/output; Python state-machine tường minh ở Coordinator, registry và quyền tool theo AgentSpec. Bắt đầu từ async dispatch có timeout/trace và stub trung thực. Không đưa orchestration framework lớn vào bootstrap. React/Vite chỉ hiển thị phạm vi và capabilities.

Hệ quả: dễ chạy local, kiểm thử và truy vết; có thể tách service sau qua versioned contracts. Timeout asyncio mang tính cooperative: tool blocking cần thread/process/worker riêng khi tích hợp. State/trace hiện trong RAM, chưa durable, chưa retry hay scheduling. Chưa có đầy đủ state transitions nghiệp vụ; cần thiết kế failure paths và safety gates trước Phase 06.

Phương án đã cân nhắc: microservices (quá nhiều vận hành), framework agent lớn (thêm dependency và làm khó chứng minh logic quyết định). Không chọn agent tự chủ gọi tool tùy ý vì cần kiểm soát safety và quyền rõ ràng.
