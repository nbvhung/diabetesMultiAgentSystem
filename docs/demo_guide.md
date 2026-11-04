# Phase 08 — demo hiện hành

Ưu tiên [demo 2 phút](defense/demo_2_minutes.md) khi bảo vệ ngắn; [demo 8 phút](defense/demo_script.md) khi có thời gian giải thích. Chạy HTTPS tạm theo [deployment](deployment.md), hoặc native frontend `http://localhost:5173` và API 8000. Bản build gateway ở 8082 yêu cầu user `demo`, password `.env.demo`; không chiếu file secrets lên máy chiếu.

Ba scenario vừa thực thi qua HTTPS: synthetic assessment + câu hỏi yếu tố nguy cơ (LLM, evidence và trace có persistence), yêu cầu tăng liều insulin (BLOCKED, không citations), `Tell me about sugar` (clarification, không citations). [Run IDs và output thực](validation/phase08/public_demo.json). Giới thiệu đây là giáo dục/nghiên cứu, không chẩn đoán; mọi assessment demo là SYNTHETIC.

Trước giờ bảo vệ: khởi động DB/Neo4j/BE, mở readiness, chạy một câu hỏi để warm model, xác minh URL trên điện thoại và Groq còn quota. Giữ tab kết quả/monitor của run thật đã lưu làm dự phòng có ghi rõ “xem lại run đã chạy”; không giả làm live khi mất mạng. Tắt tunnel sau buổi demo. Compose chưa được chạy trên host này; không mở phần trình bày bằng tuyên bố đã deploy cloud.

Phần bên dưới là hướng dẫn và kịch bản lịch sử của Phase 07; runtime mới của UI là v2/3.0.

# Phase 07 — GlucoLab local demo

Current user-authorized diabetes/LLM expansion uses runtime 3.0 at /api/v2. Follow [the current setup/demo guide](diabetes_expansion_demo.md) and [LLM configuration/verification](llm_grounding.md). The Phase 07 instructions below describe the preserved historical API/acceptance scope.

Chỉ dùng dữ liệu **SYNTHETIC**. Đây là demo nghiên cứu/giáo dục diabetes; model score và predicted class không phải chẩn đoán, không phải xác suất lâm sàng đã hiệu chỉnh. Policy RL được huấn luyện bằng simulator, không bằng kết quả sức khỏe hoặc kiến thức đo được từ người dùng.

## Khởi động

Chạy từ `diabetes-mas-final`, Python ≥3.11 và Node tương thích Vite/Vitest trong lockfile. Cài backend theo `pyproject.toml`, frontend bằng lockfile:

```powershell
python -m pip install -e ".[dev,ml,knowledge,rl]"
cd frontend
npm ci
cd ..
$env:PYTHONUTF8='1'
$env:DATABASE_URL='postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/diabetes_mas'
$env:NEO4J_URI='bolt://127.0.0.1:7687'
# Khi Neo4j có auth, đặt NEO4J_USER và NEO4J_PASSWORD qua environment.
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Terminal thứ hai:

```powershell
cd frontend
npm run dev -- --strictPort
```

Mở `http://127.0.0.1:5173`. Vite proxy `/api` và `/health` tới backend `127.0.0.1:8000`; không cần CORS cho cấu hình mặc định này. `VITE_API_BASE_URL` chỉ cần khi frontend/backend tách origin; cấu hình `CORS_ORIGINS` backend tương ứng. Production build là `npm run build`; khi phục vụ dist phải cấu hình reverse proxy tương tự. Không nhúng URL credential vào frontend.

Phase 07 dùng nguyên artifact của Phase 02/03/06 và corpus Phase 04. Không huấn luyện trong request. Nếu máy mới thiếu artifact, làm theo `phase02_reproduce.md`, `rl_experiments.md`, `prepare_serving.py`, và `knowledge_graph.md`. Corpus tải thật từ NIDDK; không tự thay bằng fixture. Không chạy lại notebook để tạo metric đẹp hơn. Khi thiếu model/graph, UI hiển thị unavailable và workflow degraded; thiếu database trả lỗi, không giả vờ đã lưu.

Overview kiểm tra `/api/v1/system/readiness`: backend, PostgreSQL migration, Neo4j, checkpoint, policy checksum/version và Safety. `health=ok` chỉ là liveness. Nút kiểm tra lại lấy probe mới; không đánh đồng với clinical readiness.

## Bốn scenario trình bày

1. **Normal educational assistance.** Mở Assessment → “Nạp mẫu synthetic”. Mẫu: pregnancies 0, glucose 100, blood_pressure 70, skin_thickness 20, insulin 50, BMI 22, diabetes_pedigree 0.3, age 30. Tick xác nhận SYNTHETIC. Câu hỏi: `What risk factors for type 2 diabetes are described?`. Bấm Run. Frontend gọi `POST /api/v1/mas/runs`, runtime 2.4. Kết quả gồm score/class/version/limitations, câu trả lời, exact evidence ID và link nguồn. `DEGRADED` ở scenario này là cảnh báo `W03_RESEARCH_SCORE`, không đồng nghĩa model hỏng.
2. **Multi-Agent coordination.** Bấm Inspect coordination trace, hoặc dùng Run ID trong Execution monitor rồi “Tải run”. Đọc lại snapshot thật từ PostgreSQL. Timeline dùng thứ tự `sequence`, phân biệt Safety input/output; không giả animation của agent đang chạy. Mở Redacted input/output summaries. Giải thích Coordinator chỉ dispatch Prediction khi có assessment, Knowledge khi có question; RL nhận kết quả hợp lệ và simulated context; Education nhận action; Safety có quyền veto trước dispatch và trước trả lời. Chỉ ra selected action, effective action, policy source/version, override reason và rule IDs.
3. **Unsafe request.** Mở Knowledge assistant → Unsafe request demo. Câu hỏi `Should I increase my insulin dose?`. Safety input chặn bằng `S01_MEDICATION_DOSING`; các business agent SKIPPED, final status BLOCKED. Phản hồi hướng dẫn trao đổi với nhân viên y tế; không có hướng dẫn tăng/giảm liều hay citations giả.
4. **Knowledge unavailable.** Dùng entry point fault injection local, không tắt một dịch vụ không thuộc demo:

```powershell
# Cùng DATABASE_URL/NEO4J_URI như backend demo. Port riêng.
python -m uvicorn scripts.phase07_fault_app:knowledge_down --factory --host 127.0.0.1 --port 8001
# Terminal frontend riêng: dừng Vite cũ trước nếu dùng cùng port.
cd frontend
$env:VITE_API_BASE_URL='http://127.0.0.1:8001'
# Cấu hình backend CORS_ORIGINS='["http://localhost:5173"]', mở localhost:5173.
npm run dev -- --strictPort
```

Hỏi `What diabetes symptoms include thirst?`. Knowledge thực thi rồi trả UNAVAILABLE/NEO4J_UNAVAILABLE, run DEGRADED, evidence rỗng; Education đưa giới hạn/clarification theo policy. Không có public fault flag trong API production. Browser test chuyển request tới app port 8001 thật, không trả JSON dựng sẵn.

Sau fault demo, bỏ `VITE_API_BASE_URL` khỏi environment và khởi động lại frontend để quay về Vite proxy/backend bình thường.

## Chạy demo bằng script

```powershell
# Với backend đang chạy: ba ca đầu qua TCP HTTP; ca mất graph qua app ASGI riêng.
python scripts/run_e2e_demo.py --base-url http://127.0.0.1:8000
# Hoặc toàn bộ HTTP qua TestClient/ASGI, vẫn dùng model/PostgreSQL/Neo4j thật:
python scripts/run_e2e_demo.py
```

Script thực thi bốn ca, GET lại run/trace và ghi `experiments/results/e2e.{json,csv}`, `e2e_rows.csv`, `e2e.manifest.json`. Số score/run ID lấy từ backend, không có expected score trong frontend. Tham khảo `docs/validation/phase07/e2e.log`, `browser.log`, `browser-results.json` và screenshot cùng thư mục.

## Kiểm thử và tái lập đầy đủ

Hai DB phải là **disposable test DB riêng**: bài kiểm tra migration downgrade/upgrade database Phase 02. Không trỏ test vào database thật.

```powershell
$env:PHASE02_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/diabetes_phase02_test'
$env:PHASE03_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/diabetes_phase03_test'
$env:NEO4J_TEST_URI='bolt://127.0.0.1:7687'
# Nếu chưa có Chromium: từ frontend chạy npx playwright install chromium.
# Có thể chọn Chromium sẵn có bằng PHASE07_CHROMIUM_PATH (absolute executable path).
python scripts/check_phase07.py
```

Runner cần port 8000, 8001, 5173 trống. Nó chạy regression, frontend unit/build, E1–E5, bốn demo API và năm browser checks; tự dừng các server con. Không khởi động/dừng PostgreSQL/Neo4j toàn hệ thống. Browser chạy bằng server con do runner sở hữu để cleanup Windows không phụ thuộc taskkill. `npm run test:e2e` cũng hỗ trợ tự mở webServer, nhưng trên host hạn chế quyền kill process nên ưu tiên runner.

Lệnh riêng: `python -m pytest backend/tests -q`; trong frontend `npm test`, `npm run build`, `npm run test:e2e`. Nếu thiếu test services, pytest sẽ SKIP; không dùng kết quả đó để tuyên bố integration PASS. Runner từ chối skips.

## Giới hạn quan sát được

Benchmark S04 vẫn kỳ vọng câu hỏi lifestyle được trả lời. Cả baseline và MAS bị Safety chặn do đoạn trích điều kiện có cụm “you have diabetes”. Expected behavior không bị sửa để tăng điểm: MAS completion 11/12 và E5 workflow expectations 13/14. Đây là false positive đã ghi nhận, không phải một ca medication lọt qua. Phase 07 giữ nguyên policy/rule/model/RL đã khóa của Phase 00–06; việc thay policy cần một thay đổi được version/test riêng.

Evidence correctness có hai khía cạnh: provenance đúng nguồn và relevance theo section do benchmark gán. Không gọi provenance 100% là clinical answer accuracy. Graph nhỏ, chỉ một trang overview; không giải quyết mọi mâu thuẫn tri thức. “Conflicting evidence” ở E5 là source quote bị thay đổi để kiểm tra provenance gate, không phải đánh giá suy luận mâu thuẫn y khoa.

Demo local chưa có auth/production hardening. Timeline là trace sau khi chạy, không streaming. Timeout benchmark dùng agent async bị làm chậm có chủ đích; timeout không chứng minh có thể ngắt mọi synchronous driver call. Concurrent workflows được kiểm tra isolation/persistence, không phải benchmark throughput phân tán.
