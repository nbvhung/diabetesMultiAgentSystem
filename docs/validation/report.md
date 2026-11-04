# Phase 00 validation report

Kết luận: **PASS — READY_FOR_PHASE_01**. Không triển khai Phase 01–08.

Thời điểm ghi báo cáo (UTC): 2026-11-01T19:54:42.284997+00:00.

## Các lệnh thực tế và kết quả

| Lệnh | Kết quả | Bằng chứng |
|---|---|---|
| `python -m pip install -e ".[dev]"` | PASS; editable install và dependency backend | Output terminal phiên làm việc; versions.log ghi versions thực tế |
| `npm install --cache .npm-cache --fetch-retries=0 --fetch-timeout=20000` trong frontend | PASS; added 21 packages, audit 22 packages, 0 vulnerabilities tại lần cài này | Output terminal; frontend/package-lock.json |
| `python scripts/run_checks.py` | PASS, exit 0 | results.json và các log bên dưới |
| `python -m pytest -v` | PASS; 19 passed, 1 warning | pytest.log |
| `python scripts/verify_phase00.py` | PASS; cây thư mục và placeholder .env.example | structure_env.log |
| `python -m alembic heads` | PASS; không có revision, đúng skeleton | alembic_heads.log |
| Import Base/engine SQLAlchemy rồi dispose | PASS; 0 business tables; không kết nối DB | db_import.log |
| `npm run build` | PASS; tsc --noEmit và Vite 7.3.7 | frontend_build.log |
| Uvicorn child + GET /health, GET /api/v1/system/capabilities | PASS; HTTP 200, health ok, prediction_agent stub | uvicorn.log, live_http.json |

`run_checks.py` chạy Uvicorn ở loopback với port tạm, ghi log rồi terminate đúng child process đã tạo. Không để server chạy nền sau kiểm chứng. Cách chạy server phát triển liên tục có trong README.

Môi trường: Python 3.11.9, Node v24.14.1, npm 11.11.0. Phiên bản Python packages trong versions.log. Cài Python lần này sử dụng interpreter hiện có; README hướng dẫn venv để chạy độc lập. Các optional ML/knowledge dependencies chưa cài hoặc xác minh.

## Sự cố đã gặp và xử lý

- Probe đầu tiên cho thấy thiếu SQLAlchemy; cài dependency khai báo trong pyproject đã thành công.
- Lệnh tạo source đầu tiên ghi file thành công nhưng print đường dẫn Unicode lỗi cp1252. Đã dùng UTF-8 khi tạo tài liệu và ghi lại frontend tiếng Việt; source được import/build/kiểm thử sau đó thành công.
- npm install mặc định không hoàn tất; dừng phiên đó. Lần thử dùng cache local ghi nhận EACCES khi truy cập registry dưới sandbox. Chạy lại với quyền mở rộng đã được cấp, cùng cache local: thành công. Cache local bị ignore.
- Một lần gọi run_checks từ thư mục cha trả file-not-found; chạy lại từ project root đúng hướng dẫn và PASS.
- 1 warning từ Starlette TestClient: httpx backend bị deprecate ở phiên bản đã cài; tests vẫn PASS. Không thay đổi thêm dependency ngoài bộ đã thống nhất chỉ để tắt cảnh báo.

## Giới hạn

- Agent/coordinator vẫn stub; test success output chỉ kiểm tra contract bằng fixture có nhãn synthetic, không có inference hay kết quả y khoa thật.
- DB engine import và Alembic heads không chứng minh PostgreSQL kết nối được. Docker/PostgreSQL chưa chạy; không business schema. Capabilities database=unavailable.
- Chưa có DL, Neo4j/RAG, safety rules nghiệp vụ, RL policy, workflow end-to-end, auth hoặc đánh giá lâm sàng.
- Frontend đã build; chưa kiểm tra tương tác bằng browser tự động. Home chỉ hiển thị capabilities thật từ API hoặc báo lỗi kết nối.
- Secret check có phạm vi .env.example: placeholder và một số pattern key phổ biến; không thay thế kiểm toán secret tổng quát.
- Trace trong RAM; asyncio timeout chỉ phù hợp tác vụ cooperative. Không có model, metric, biểu đồ huấn luyện hoặc dữ liệu bệnh nhân được tạo.
- Repository cha chưa khởi tạo Git. Không git init, không commit, không push. Commit hash: không có.
- Traceability dựa trên yêu cầu người dùng, chưa xác minh rubric gốc giảng viên. Phase 01–08 là kế hoạch đề xuất và chưa được thực hiện.

## File được tạo

Xem [inventory.txt](inventory.txt): danh sách source/config/docs/.gitkeep; loại trừ node_modules, build output, cache và editable-install metadata. Không sửa assignment cũ.
