# Current Phase 06 review fixes

Runtime 2.4 rejects invalid RL actions before Education. Validation/evaluation/serving share the same selector; Education records proposed/effective action + override reason. Two Safety gates remain authoritative. ADR 0006 and the remediation report supersede earlier 2.3 notes below. No Phase 07 work.

# Phase 06 current workflow

Input Safety → Prediction/Knowledge as appropriate → integrated RL educational decision (including empty-data clarification) → action-driven grounded Education → output Safety → persisted response/trace. Policy version/action/source are traced. Two veto gates and no-retraining constraints preserved. Runtime 2.3; [MDP](rl_mdp.md), [ADR 0005](decisions/0005-educational-rl.md). Older phase descriptions follow as history.

# Phase 05 current workflow

Safety now runs before any business action and again before final response, with a latched veto and versioned decisions. All current run paths, including scaffold fixtures, enforce both. See [policy and sequence](safety_policy.md) and [rule catalog](rule_catalog.md). Runtime 2.2/SafetyDecision 1.1 supersede historical examples below. Input denial skips all business agents; final gate cannot revive denied work.

# Phase 01 — Multi-Agent Core MVP

Runtime chạy tuần tự, mỗi request tạo registry/agent instances mới và WorkflowState mới. Coordinator cũng có thể dùng lại với các agent stateless; kiểm thử concurrent xác minh state không bị trộn. Runtime không gọi LLM, model, graph hoặc policy thật.

```mermaid
sequenceDiagram
    participant U as API client
    participant API as FastAPI
    participant C as Coordinator
    participant P as Prediction (stub)
    participant K as Knowledge (stub)
    participant R as RL (stub)
    participant E as Education (minimal)
    participant S as Safety (minimal)
    participant DB as InMemoryRunRepository
    U->>API: POST /api/v1/mas/runs (assessment and/or question)
    API->>API: Validate RunInput v2.0
    API->>C: run(validated input), new run_id
    opt assessment exists
        C->>P: typed PredictionTask
        P-->>C: UNAVAILABLE, no prediction
    end
    opt question exists
        C->>K: typed KnowledgeTask
        K-->>C: UNAVAILABLE, no evidence
    end
    alt compatible policy and valid context (future injection)
        C->>R: RLTask
        R-->>C: terminal result
    else no policy (default)
        C->>C: RL UNAVAILABLE, no tool invocation
    end
    C->>E: EducationTask with valid outputs only
    E-->>C: COMPLETED, transparent abstention
    C->>S: SafetyTask(original question, candidate)
    S-->>C: COMPLETED with allowed/veto
    alt veto or safety failure
        C->>C: withhold candidate and redact education output
    else allowed
        C->>C: use safe candidate; DEGRADED if dependencies unavailable
    end
    C-->>API: WorkflowResponse + trace + warnings
    API->>DB: save deep copy (bounded, process local)
    API-->>U: 201 + terminal run
    U->>API: GET run / GET trace
    API->>DB: get snapshot by run_id
    DB-->>API: deep copy or missing
    API-->>U: 200 or 404
```

## Phân biệt agent, tool và Coordinator

Agent là đơn vị quyết định có AgentDefinition, input/output schema, execute(message), timeout và fallback policy riêng. Tool là khả năng ngoài agent, ví dụ torch inference hoặc Neo4j read; Phase 01 không cấp tool nào (`permitted_tools=[]`). Minimal safety rules là logic nội bộ, không phải engine/tool bên ngoài. Coordinator quyết định agent nào được chạy dựa trên request và trạng thái khả dụng/kết quả; tạo message, kiểm tra output, timeout, chuyển trạng thái, tổng hợp trace và áp safety gate. Repository không phải agent.

`BaseAgent` là Protocol; `AgentRegistry` từ chối đăng ký trùng và timeout không hợp lệ. Registry không tự chạy agent. Metadata công khai qua `/agents` cho biết JSON schema và thực trạng stub/minimal, không chỉ tên class.

## Quyết định điều phối

1. API từ chối request thiếu cả assessment và question, question trắng/quá dài, assessment thiếu/không hợp lệ (422). Assessment dùng nguyên contract Pima v1.0; không suy diễn feature còn thiếu.
2. Có assessment: gọi Prediction; thiếu assessment: SKIPPED/NO_ASSESSMENT và không gọi. Stub được gọi trả UNAVAILABLE/TOOL_NOT_INTEGRATED.
3. Có question: gọi Knowledge; thiếu question: SKIPPED/NO_QUESTION. Stub trả UNAVAILABLE, evidence rỗng.
4. Không policy khả dụng: Coordinator đánh dấu RL UNAVAILABLE/NO_COMPATIBLE_POLICY, không gọi policy. Nếu registry có policy được đánh dấu available nhưng không có prediction/evidence hợp lệ: SKIPPED/NO_VALID_POLICY_CONTEXT. Chỉ khi đủ cả policy lẫn context mới gọi RL. Nhánh này chỉ được kiểm thử bằng fixture SYNTHETIC, không có policy thật trong app.
5. Education luôn chạy nếu Coordinator đã bắt đầu. Chỉ nhận output đúng kiểu của agent hoàn tất. Phase 01 chỉ tạo abstention minh bạch, không dùng template để dựng lời giải thích y khoa, không nhại lại câu hỏi hoặc tạo citation. Không tự diễn giải 8 feature thành nguy cơ.
6. Safety luôn chạy sau education/fallback và nhận câu hỏi gốc cùng candidate. UNAVAILABLE/FAILED/timeout ở safety → FAILED và fail closed. Veto → BLOCKED với lời từ chối cố định. COMPLETED của Safety chỉ có nghĩa rule evaluation xong, không có nghĩa allowed=true.
7. Khi được phép phát hành, dùng candidate. Nếu có agent unavailable/failed, workflow DEGRADED. COMPLETED chỉ có thể xảy ra khi đủ đường đi cần thiết, không có dependency warning; bản mặc định thường DEGRADED vì RL chưa tích hợp. Dù DEGRADED/BLOCKED/FAILED vẫn là run hợp lệ nên POST trả 201, status nằm trong body.

## Safety tối thiểu

- S01_MEDICATION_DOSING: dấu hiệu hỏi/đổi liều cùng thuật ngữ thuốc trong câu hỏi, tiếng Việt không dấu/có dấu và một số tiếng Anh.
- S02_DIAGNOSTIC_CERTAINTY: cụm khẳng định chắc chắn trong candidate.
- S03_OUTPUT_DOSAGE: số và đơn vị thuốc trong candidate.

Đây là lexical rules bảo thủ, có false positives/false negatives, không đủ cho triển khai y khoa công khai. Ví dụ câu hỏi giáo dục về liều có thể bị veto. Không tích hợp rule engine đầy đủ (Phase 05). Từ chối là thông báo giới hạn hệ thống, không phải chỉ dẫn điều trị. Safety timeout/mất agent luôn chặn phát hành. Candidate bị chặn được thay bằng `[WITHHELD_BY_SAFETY]` cả trong agent_results, tránh rò qua GET/POST. Citation ID không có trong knowledge evidence → FAILED và giữ lại nội dung.

## Trạng thái và trace

Agent: NOT_STARTED → RUNNING → COMPLETED/FAILED/UNAVAILABLE; hoặc NOT_STARTED → SKIPPED/UNAVAILABLE khi Coordinator không thể/không cần dispatch. Terminal không được chạy lại trong cùng run. Timeout ánh xạ FAILED + AGENT_TIMEOUT (không thêm enum TIMEOUT trái yêu cầu). Workflow: NOT_STARTED → RUNNING → COMPLETED/DEGRADED/BLOCKED/FAILED. Hàm chuyển trạng thái từ chối cạnh không hợp lệ.

Trace có sequence tăng, run_id, agent_id (null cho workflow), message_id (cùng ID cho RUNNING và terminal khi đã dispatch), UTC aware timestamp, status và mã reason. Trace không chứa input, exception text hay candidate. SKIPPED/UNAVAILABLE không dispatch có message_id=null; không tạo message giả. Log chỉ chứa run_id/agent/status và mã lỗi, không thông tin bệnh nhân.

Timeout dùng asyncio.wait_for, cooperative; blocking tool phải có worker/thread/process ở phase tích hợp. Không retry, không chạy agent song song. Client disconnect/cancellation không lưu partial run; POST hiện đồng bộ đến terminal, không background job, GET không công bố state đang chạy.

## Storage và phạm vi vận hành

RunRepository Protocol có save/get, implementation app-owned InMemoryRunRepository. Có RLock, deep copy khi save/get, capacity 100, loại run lưu cũ nhất khi đầy. Chỉ lưu response cuối (không lưu request/assessment), vẫn chứa nội dung kết quả nhạy cảm nếu sau này tích hợp. Không có biến toàn cục lưu state theo run. Các app instance không chia sẻ repository; nhiều worker cũng không chia sẻ. Restart/eviction mất run, GET trả 404. Không TTL hoặc persistence; PostgreSQL repository dành Phase 03, chưa làm ở đây.

Chưa auth/authorization, chỉ chạy local với dữ liệu synthetic. Không dùng endpoints này với thông tin bệnh nhân thật. Không mở deployment production.

## Demo và kiểm thử

```powershell
# Từ diabetes-mas-final
python -m pytest backend/tests -v
python scripts/demo_mas.py
python scripts/check_phase01.py
```

Demo gọi API ASGI thật qua TestClient, không mở server, lưu JSON tại docs/validation/phase01/demo.json. A: câu hỏi → Knowledge UNAVAILABLE, Education/Safety COMPLETED, DEGRADED. B: assessment SYNTHETIC → Prediction UNAVAILABLE, Education/Safety COMPLETED, DEGRADED. C: hỏi tăng liều insulin → Safety veto, BLOCKED. Prediction/evidence đều rỗng; agent metadata ghi rõ stub/minimal. check_phase01 còn mở Uvicorn tạm và gọi HTTP thật để kiểm chứng run/read/trace/agents.
