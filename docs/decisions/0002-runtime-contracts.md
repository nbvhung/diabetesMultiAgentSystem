# ADR 0002 — Versioned Phase 01 runtime and in-memory runs

Trạng thái: chấp nhận. Ngày: 2026-11-02.

Yêu cầu Phase 01 mới thay kế hoạch đề xuất trước đó: Phase 01 là MAS Core MVP, PostgreSQL run persistence ở Phase 03 và full rule engine ở Phase 05. Không triển khai các phần đó ở lượt này.

v1.0 WorkflowState bắt buộc assessment và v1.0 AgentResult dùng success/stub/error/timeout, không tương thích yêu cầu mới question-only và lifecycle NOT_STARTED/RUNNING/COMPLETED/SKIPPED/FAILED/UNAVAILABLE. Không đổi âm thầm contract cũ.

Quyết định: giữ nguyên schemas/contracts.py v1.0; thêm schemas/runtime.py v2.0 cho RunInput, typed tasks/messages, lifecycle, workflow state và response. Schema output nghiệp vụ (AssessmentInput, PredictionResult, EvidenceItem, KnowledgeOutput, EducationOutput, RLDecision, SafetyDecision) vẫn nhúng v1.0. Runtime result validator khóa output theo agent, cấm stub COMPLETED và cấm business output ở trạng thái khác COMPLETED. Kiểm tra identity khi Coordinator nhận result.

Không có run v1 lưu trữ, không có endpoint workflow v1 cũ nên không cần DB migration/backfill. Không có implicit converter v1→v2: caller v1 tiếp tục dùng module contracts và legacy coordinator scaffold; endpoint MAS mới chỉ nhận v2.0 (default nếu client không gửi schema_version). Gửi schema_version=1.0 vào MAS API trả 422. Public legacy coordinator scaffold chuyển sang mas/legacy.py; import Python mới là mas/coordinator.py:Coordinator. Test Phase 00 dùng legacy module và vẫn chạy, chứng minh contract v1 không đổi. mas/state.py giữ aliases v1; các runtime types import rõ ràng từ schemas/runtime.py.

Repository theo Protocol, nằm trên app.state do create_app tạo, không global dict theo run. save/get deep-copy dưới RLock, bounded 100 runs. POST synchronous chạy đến terminal rồi lưu; GET running status/background execution không thuộc phạm vi. Mất dữ liệu khi restart/eviction và tách biệt worker là giới hạn công bố, không ngụy tạo persistence.

Chỉ triển khai Education abstention và Safety lexical gate có kiểm thử. Các agent tool-dependent không trả inference/citation/action giả. Không gọi RL khi không có policy; terminal UNAVAILABLE do Coordinator ghi rõ reason, khác với task đã dispatch có message_id. Fail closed nếu Safety không thể đánh giá.

Hệ quả: API thực thi được và kiểm thử cô lập, giữ tương thích dữ liệu v1.0. Cần thiết kế task schema/version tiếp khi thêm model/RAG/policy; cần auth/retention và persistent repository trước dữ liệu nhạy cảm. Trace chỉ mã sự kiện không chứa dữ liệu người dùng.
