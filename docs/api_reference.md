# API reference — runtime hiện hành

Nguồn chuẩn: `/openapi.json` trên backend và `backend/app/research/{api,schemas}.py`. Runtime mới là **3.0 qua `/api/v2`**; `/api/v1` MAS giữ 2.4 cho dữ liệu lịch sử. Version API, workflow, prediction và policy là các khái niệm khác nhau. Prediction serving 1.1; Safety `diabetes-safety-2.0`.

| Method / path | Input | Output / ý nghĩa |
|---|---|---|
| GET `/health` | Không | Liveness; không chứng minh dependency đã sẵn sàng |
| GET `/api/v2/system/readiness` | Không | checked_at và status/code/version theo component; không chứa credentials |
| GET `/api/v2/mas/agents` | Không | Typed definitions, quyền tool, timeout và fallback |
| POST `/api/v2/mas/runs` | Assessment synthetic và/hoặc question, language vi/en | 201 chỉ sau commit; WorkflowResponse 3.0 |
| GET `/api/v2/mas/runs/{uuid}` | Run UUID | Snapshot đã lưu; không tự tạo workflow mới |
| GET `/api/v2/mas/runs/{uuid}/trace` | Run UUID | Ordered events cùng run_id/schema version |
| GET `/api/v2/knowledge/sources` | Không | Registered source URLs, source hash, chunk count và retrieved_at |
| GET `/api/v2/knowledge/graph` | Không | Release-bound graph summary và assertion metadata |
| POST `/api/v2/knowledge/search` | SearchInput theo OpenAPI | Kiểm tra retrieval; không phải câu trả lời cuối của Coordinator |
| GET `/api/v1/experiments` | Không | Các bundle hoàn chỉnh đã kiểm checksum; thiếu → unavailable |
| GET `/api/v1/experiments/{name}/figure` | Tên allowlisted | PNG trong manifest; không phải metric/ảnh giả thay thế |

Kiểm tra method search theo OpenAPI của đúng version đang chạy trước khi dùng script riêng. UI chính chỉ tạo câu trả lời qua Coordinator, không gọi riêng search rồi tự ghép kết quả.

```json
{
  "schema_version": "3.0",
  "language": "vi",
  "question": "Bệnh tiểu đường týp 2 có những yếu tố nguy cơ nào?",
  "is_synthetic": true,
  "assessment": {
    "pregnancies": 0, "glucose": 100, "blood_pressure": 70,
    "skin_thickness": 20, "insulin": 50, "bmi": 22,
    "diabetes_pedigree": 0.3, "age": 30
  }
}
```

Ví dụ trên **SYNTHETIC**, không phải hồ sơ thật. Không có response JSON “mẫu thành công” dựng sẵn; xem [actual HTTPS runs](validation/phase08/public_demo.json). Response có `run_id`, `status`, `response`, `evidence`, sáu `agent_results`, `agent_trace`, hai `safety_decisions`, `warnings`, `limitations`, `generation_mode`, `grounding`, `retrieval_rounds`, `corpus_version`.

`generation_mode`: llm / extractive / clarification / withheld. `DEGRADED` có thể là đã phát hành nội dung giáo dục hợp lệ nhưng mang research-score warning hoặc fallback; không tự đổi nhãn thành lỗi mạng. `BLOCKED` nghĩa là nội dung bị ngăn; `FAILED` gồm fail-closed hoặc lỗi workflow. Agent lifecycle có COMPLETED/UNAVAILABLE/FAILED/SKIPPED; một agent thành công không đồng nghĩa workflow lâm sàng an toàn.

HTTP: 422 input sai, 404 không có run, 409 snapshot legacy cần review, 503 persistence/workflow không sẵn sàng. Lỗi nội bộ được sanitize; không trả exception/connection string. Server timeout theo agent và deadline Coordinator; client dùng 120 giây. Trace là post-run, không streaming. GET không có danh sách toàn bộ bệnh nhân/run; UUID không thay thế authorization trong triển khai production.

Cổng demo thêm Basic auth `demo` + password `.env.demo`, trả 401/413/429/503 theo boundary của gateway và không mở mọi API. Backend local API chưa có hệ tài khoản người dùng; không công khai trực tiếp cổng 8000.
