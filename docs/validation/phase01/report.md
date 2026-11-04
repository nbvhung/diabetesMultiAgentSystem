# Phase 01 — Validation report

**PASS — READY_FOR_PHASE_02**. Chỉ thực hiện Phase 01 Multi-Agent Core MVP theo yêu cầu mới; không triển khai phase khác.

Thời điểm kiểm chứng UTC: 2026-11-01T20:04:57.734291+00:00. Báo cáo ghi UTC: 2026-11-01T20:06:14.168349+00:00.

## Kết quả lệnh thực tế

Từ project root `diabetes-mas-final`, chạy `python scripts/check_phase01.py`: exit 0. Script thực thi và ghi log cho:

| Lệnh / kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| `python -m pytest backend/tests -v` | **48 passed**, 1 warning; gồm 19 test nền v1 và 29 test runtime/API | [pytest.log](pytest.log) |
| `python scripts/demo_mas.py` | **PASS**, A/B DEGRADED, C BLOCKED | [demo.log](demo.log), [demo.json](demo.json) |
| `python scripts/verify_phase00.py` | **PASS**, cấu trúc + placeholder .env.example | [structure_env.log](structure_env.log) |
| `npm run build` trong frontend | **PASS**, TypeScript và Vite | [frontend_build.log](frontend_build.log) |
| Uvicorn child + HTTP thật | **PASS**, health/capabilities, POST run, GET run, GET trace, GET agents | [uvicorn.log](uvicorn.log), [live_http.json](live_http.json) |

Kết quả có cấu trúc: [results.json](results.json). HTTP live dùng port loopback tạm; script terminate đúng child process đã tạo sau kiểm tra. Không để server chạy nền. Không cài thêm dependency ở Phase 01.

## Acceptance criteria

- Request tạo UUID run_id và trace có sequence/correlation ID.
- A thực thi Knowledge (UNAVAILABLE), Education và Safety (COMPLETED); B thực thi Prediction (UNAVAILABLE), Education và Safety; có trên hai agent thực sự được await, không chỉ khởi tạo object.
- Coordinator phân nhánh assessment/question/policy-context. Không assessment thì Prediction SKIPPED, không dispatch. Không policy thì RL UNAVAILABLE, không giả lập hành động.
- State transitions được kiểm tra, terminal không được chạy lại. Timeout → FAILED/AGENT_TIMEOUT; exception/invalid result → FAILED bằng mã lỗi không lộ exception text.
- Knowledge/Prediction/RL có metadata implementation=stub và không output nghiệp vụ. Education là abstention thực thi được; Safety là lexical rule gate thực thi được.
- Safety veto hoặc failure giữ lại candidate, redact Education output trong response/store. Citation không có nguồn bị giữ lại. Không fake medical results/citations.
- Concurrent tests: 20 coordinator runs dùng chung coordinator và 12 async HTTP requests, UUID/trace/warnings/outputs cô lập. Repository copy/eviction và app isolation được kiểm tra.
- 4 endpoint MAS hoạt động, input invalid trả 422, missing run trả 404, CORS POST có kiểm tra.

## Demo thực tế, toàn bộ dữ liệu SYNTHETIC

- `A_SYNTHETIC_EDUCATION`: run_id=`cecf32b0-b9c4-45dc-8686-ced741285afb`, status=`DEGRADED`.
- `B_SYNTHETIC_ASSESSMENT_NO_MODEL`: run_id=`c9da213d-1d24-4d24-84c2-e7b88a67caf2`, status=`DEGRADED`.
- `C_SYNTHETIC_UNSAFE_MEDICATION_REQUEST`: run_id=`9f73baed-95b2-4026-9cee-ddc5c21b89b4`, status=`BLOCKED`.

Mỗi case evidence=[], prediction output=None; JSON gắn nhãn không phải bệnh nhân/kết quả y khoa thật. RL UNAVAILABLE. A/C không assessment nên prediction SKIPPED; B có assessment nên Prediction được gọi và UNAVAILABLE. Metadata demo ghi input/output schemas, stub/minimal và fallback/timeout cho cả 5 agent.

## Contract và thay đổi

Giữ nguyên schemas/contracts.py v1.0. Thêm schemas/runtime.py v2.0 vì input question-only và lifecycle mới không tương thích v1. [ADR 0002](../../decisions/0002-runtime-contracts.md) giải thích version/migration; không có dữ liệu persisted v1 cần backfill. Legacy coordinator được giữ nguyên ở mas/legacy.py; test cũ chỉ đổi import để kiểm tra scaffold v1. Metadata và contract mới được mô tả trong agent_contracts.md và mas_workflow.md.

Danh sách đầy đủ file mới/sửa và log ở [files.txt](files.txt). Không sửa assignment cũ; không làm PostgreSQL persistence, training, graph/RAG hay policy thật. Không thêm dependency.

## Giới hạn và các vấn đề đã xử lý

- Education chỉ trả abstention minh bạch, chưa tạo nội dung giáo dục có nguồn. COMPLETED là hoàn thành nhiệm vụ giới hạn, không phải tích hợp LLM/RAG.
- Safety là lexical rules S01/S02/S03, có thể bỏ sót/chặn nhầm; chưa phải rule engine đầy đủ hoặc xác minh y khoa. Tool permissions rỗng. Full engine thuộc Phase 05.
- Prediction/Knowledge/RL vẫn stub; nhánh có policy/context chỉ dùng fixture SYNTHETIC trong test, không bật trong app/demo.
- RAM repository max 100, loại run lưu cũ nhất; mất dữ liệu khi restart, không chia sẻ worker, không TTL. POST chạy synchronous đến terminal; không background/running-run query và không partial-run persistence. PostgreSQL repository thuộc Phase 03, chưa làm.
- Chưa auth/authorization, clinical validation hoặc dùng với dữ liệu bệnh nhân thật. Chỉ local/synthetic.
- Timeout asyncio chỉ cooperative; blocking tool cần worker/thread/process khi tích hợp sau.
- Cảnh báo deprecation TestClient/httpx từ dependency đã có, không làm test thất bại.
- Lần test runtime đầu có 47 PASS/1 FAIL: fixture SyntheticPolicy bị constructor lớp stub ghi đè metadata available; sửa fixture injection và chạy lại, 48 PASS. Không có policy thật được thêm.
- Một lần pytest vô tình gọi từ thư mục cha đã được dừng; các kết quả công bố chỉ từ `backend/tests` trong project root. Không dùng kết quả assignment ngoài project.
- Git chưa khởi tạo (`git rev-parse --is-inside-work-tree` báo not a git repository); không commit, không push. Commit hash: không có.

Không chuyển sang Phase 02 trong lượt này.
