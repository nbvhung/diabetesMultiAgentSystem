# Diabetes Multi-Agent Intelligent Support System

Repository lưu source, notebooks, tài liệu Markdown, CSV/JSON và manifest thực nghiệm. Ảnh/biểu đồ, PDF/Word, dataset, checkpoint, retrieval weights, cache và secrets được ignore; các file vẫn còn trên máy. Font WOFF2 nhỏ cần cho UI được giữ cùng license. Để chạy từ clone mới, xem [installation](docs/installation.md) và dùng artifact bundle local hoặc chuẩn bị/train lại. Những link ảnh/PDF sẽ chỉ mở được khi đã cung cấp các artifact tương ứng. `.gitattributes` giữ nguyên bytes để không làm sai SHA256 trong manifest.

**Phase 08:** bản demo HTTPS tạm đã kiểm chứng; đóng gói Docker đã có nhưng chưa chạy được trên máy hiện tại vì thiếu Docker engine/WSL. Không coi đây là cloud hosting hoặc nghiệm thu 100%.

- [Báo cáo 5 chương, DOCX/PDF và hình/bảng](docs/report/README.md).
- [Đối chiếu yêu cầu của thầy trước báo cáo](docs/phase08_scope_audit.md).
- [Cài đặt từ source mới — đủ 12 bước, checkpoint hoặc train lại](docs/installation.md).
- [Docker, HTTPS tạm và giới hạn triển khai](docs/deployment.md).
- [Demo 2 phút](docs/defense/demo_2_minutes.md), [kịch bản 8 phút](docs/defense/demo_script.md), [câu hỏi bảo vệ](docs/defense/qa.md).
- [Kết quả kiểm chứng Phase 08](docs/validation/phase08/report.md), [trạng thái cuối](docs/phase_status.md).

Demo được kiểm tra ngày 03/11/2026: **https://champion-sonic-dept-charged.trycloudflare.com** — user `demo`, password đọc từ `.env.demo` trên máy bạn. URL tạm chỉ còn hoạt động khi máy/backend/gateway/tunnel đang chạy. Không đưa password/key vào Git.

Với môi trường đã chuẩn bị và BE đang chạy:

```powershell
npm --prefix frontend run build
python scripts/demo_host.py start --tunnel
python scripts/demo_host.py status
```

Nếu demo đang chạy, chỉ dùng `status`. Cấu hình Docker toàn bộ nằm ở **compose.yaml tại root**:

```powershell
python scripts/setup_compose_env.py
# Thêm Groq key vào .env.compose; chỉ tạo file nếu chưa tồn tại.
docker compose --env-file .env.compose config --quiet
docker compose --env-file .env.compose up --build --wait
```

Các lệnh native đã dùng trên máy này được giữ bên dưới để thuận tiện vận hành. Những mục phase cũ phía cuối là bằng chứng lịch sử, không phải mô tả runtime hiện hành.

# Lệnh chạy dự án trên Windows

Hướng dẫn chạy web GlucoLab với **React/Vite + FastAPI + PostgreSQL + Neo4j + Groq**. Dùng PowerShell trong VS Code hoặc Windows Terminal. Dữ liệu nhập assessment phải là **SYNTHETIC**; kết quả model phục vụ nghiên cứu/giáo dục về diabetes.

Thư mục dự án trên máy hiện tại:

```text
D:\phát triển ht thông minh\diabetes-mas-final
```

Máy hiện tại đã có thư viện, `.env`, model MLP, RL policy, corpus và model retrieval. Bắt đầu từ **[chạy thường ngày](#1-chạy-thường-ngày)**. Phần **[cài đặt lần đầu](#4-cài-đặt-lần-đầu-hoặc-khi-thiếu-dữ-liệu)** dùng khi cần chuẩn bị lại môi trường. Tài liệu các phase cũ được thu gọn ở cuối README.

Giao diện hiện tại tham khảo trang chủ **Nutriwise**: font **Be Vietnam Pro**, màu emerald/teal, nền sáng, card bo tròn và sidebar đồng bộ. Có gợi ý chủ đề bằng tiếng Việt, citations từ API, hành trình agent riêng và màn nghiên cứu có bộ lọc. [Xem ảnh desktop/mobile và kiểm chứng giao diện](docs/validation/nutriwise_ui/report.md). [Rà soát hiệu quả train và việc cần làm tiếp](docs/project_review_uiux.md) phân tích các kết quả DL/RL/RAG/MAS đã đo và giới hạn hiện tại.

## 1. Chạy thường ngày

Thứ tự: **PostgreSQL → Neo4j → Backend → Frontend → mở web**. Giữ hai terminal BE và FE hoạt động trong lúc sử dụng web. Các lệnh dưới đây dùng Python đã cài đủ dependency; nếu bạn sử dụng virtualenv thì kích hoạt đúng môi trường đó trong terminal BE trước khi chạy.

### Bước 1 — Kiểm tra PostgreSQL

```powershell
Get-Service -Name postgresql-x64-17
```

Service trên máy hiện tại là `postgresql-x64-17`; trạng thái cần là `Running`. Nếu đang `Stopped`, mở **PowerShell bằng Run as administrator**, chạy:

```powershell
Start-Service -Name postgresql-x64-17
```

Backend kết nối bằng `DATABASE_URL` trong file `.env`. PostgreSQL phải có database tương ứng với URL đó. Nếu cài PostgreSQL trên máy khác, tìm tên service thực tế bằng `Get-Service -Name '*postgres*'` và thay tên trong lệnh trên.

### Bước 2 — Terminal BE: bật Neo4j, migrate và chạy backend

Mở một terminal PowerShell và chạy lần lượt:

```powershell
cd "D:\phát triển ht thông minh\diabetes-mas-final"
$env:PYTHONUTF8='1'

python scripts/local_neo4j.py start
python scripts/local_neo4j.py status

python -m alembic upgrade head
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

- Chờ Neo4j báo `"status": "available"` trước khi chạy tiếp. Lượt bật instance có thể mất khoảng 15–30 giây; nếu lệnh báo lỗi thì xử lý lỗi trước khi bật BE.
- `alembic upgrade head` tạo/cập nhật bảng cần thiết; có thể chạy lại khi database đã ở revision mới nhất. Lệnh này không huấn luyện model.
- Chờ Uvicorn báo đang chạy tại `http://127.0.0.1:8000`. **Giữ terminal BE mở**. Chỉ mở terminal FE khi backend đã khởi động thành công.

Neo4j cũng có thể bật bằng cách nhấp đúp [start_neo4j.cmd](start_neo4j.cmd) trong File Explorer. Sau mỗi lần khởi động lại Windows, cần bật lại instance này; hiện chưa cài Windows Service tự khởi động cho Neo4j.

### Bước 3 — Terminal FE: chạy frontend

Mở **terminal PowerShell thứ hai**, chạy:

```powershell
cd "D:\phát triển ht thông minh\diabetes-mas-final\frontend"
npm run dev -- --strictPort
```

**Giữ terminal FE mở**. `--strictPort` giữ đúng cổng 5173 và báo lỗi nếu cổng đang bị chiếm. Vite đã cấu hình proxy `/api` và `/health` tới backend cổng 8000.

### Bước 4 — Mở web

Mở **[http://127.0.0.1:5173](http://127.0.0.1:5173)** trên chính máy Windows chạy dự án. Vào **Overview → Kiểm tra lại** để xem trạng thái kết nối, rồi dùng Assessment hoặc Knowledge assistant.

| Địa chỉ / cổng | Dùng để làm gì? |
|---|---|
| [http://127.0.0.1:5173](http://127.0.0.1:5173) | **Web chính của dự án — FE** |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI để xem/thử API backend |
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Kiểm tra tiến trình backend đang phục vụ HTTP |
| [http://127.0.0.1:8000/api/v2/system/readiness](http://127.0.0.1:8000/api/v2/system/readiness) | Kiểm tra các dependency thực tế của runtime hiện tại |
| [http://127.0.0.1:7474/browser/](http://127.0.0.1:7474/browser/) | Neo4j Browser để xem/chạy truy vấn graph |
| `bolt://127.0.0.1:7687` | Kết nối Neo4j từ backend; đây không phải trang web |
| `127.0.0.1:5432` | Cổng PostgreSQL thường dùng; cấu hình thực tế theo `DATABASE_URL` |

## 2. Kiểm tra nhanh và đăng nhập Neo4j

Chạy trong một terminal khác khi BE đang hoạt động:

```powershell
cd "D:\phát triển ht thông minh\diabetes-mas-final"
python scripts/local_neo4j.py status
python -m alembic current

Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v2/system/readiness | ConvertTo-Json -Depth 6
```

`/health` chỉ xác nhận backend đang chạy. Đọc `components` trong `/api/v2/system/readiness` để kiểm tra PostgreSQL, graph, model, policy, encoder, reranker và Groq. Lần đầu sau khi bật backend, việc load các model CPU có thể mất thêm thời gian.

Groq có thể hiện `configured_unverified` sau mỗi lần khởi động BE; trạng thái chuyển thành `available` sau một lời gọi provider thành công. Một workflow có thể hiện `DEGRADED` do cảnh báo `W03_RESEARCH_SCORE` dù cả sáu agent hoàn thành: model score là đầu ra nghiên cứu, không phải chẩn đoán.

Đăng nhập [Neo4j Browser](http://127.0.0.1:7474/browser/):

| Trường | Giá trị |
|---|---|
| Connection URI | `bolt://127.0.0.1:7687` |
| Username | `neo4j` |
| Password | Giá trị `NEO4J_PASSWORD` trong `.env`; bỏ dấu nháy bao ngoài |
| Database | `neo4j`, nếu được hỏi |

Thử đếm các đoạn kiến thức của corpus hiện tại:

```cypher
MATCH (e:DiabetesEvidence)
RETURN count(e) AS evidence_chunks;
```

Instance đã chuẩn bị có **449 đoạn từ 14 nguồn NIDDK**. Xem các quan hệ kiến thức:

```cypher
MATCH p=(s:DiabetesConcept)-[:HAS_RISK_FACTOR|HAS_SYMPTOM|SCREENED_WITH|HAS_COMPLICATION]->(o:DiabetesConcept)
RETURN p LIMIT 30;
```

## 3. Dừng hoặc khởi động lại

- **Dừng FE:** nhấn `Ctrl+C` trong terminal FE.
- **Dừng BE:** nhấn `Ctrl+C` trong terminal BE.
- **Dừng Neo4j:** chạy lệnh bên dưới từ thư mục dự án. PostgreSQL Windows Service thường được giữ chạy nền.

```powershell
cd "D:\phát triển ht thông minh\diabetes-mas-final"
python scripts/local_neo4j.py stop
```

Để bật lại Neo4j:

```powershell
python scripts/local_neo4j.py start
python scripts/local_neo4j.py status
```

Sau khi sửa `.env`, dừng BE bằng `Ctrl+C` rồi chạy lại lệnh Uvicorn ở bước 2 để nạp cấu hình mới.

## 4. Cài đặt lần đầu hoặc khi thiếu dữ liệu

### Cài thư viện

Chỉ cần thực hiện khi môi trường chưa có dependency hoặc dependency thay đổi:

```powershell
cd "D:\phát triển ht thông minh\diabetes-mas-final"
python -m pip install -e ".[dev,ml,knowledge,rl,semantic]"

cd frontend
npm ci
cd ..
```

### Chuẩn bị .env

Nếu `.env` chưa tồn tại:

```powershell
if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}
```

Các giá trị thật nằm trong `.env` tại thư mục gốc dự án. File `.env` hiện tại đã được cấu hình; giữ nguyên key/mật khẩu khi đọc các ví dụ.

| Biến | Ý nghĩa |
|---|---|
| `DATABASE_URL` | URL PostgreSQL dạng `postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/diabetes_mas`; dùng thông tin database của bạn |
| `NEO4J_URI` | `bolt://127.0.0.1:7687` cho instance local đã tạo |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Tài khoản Neo4j; script setup đã ghi mật khẩu thật vào `.env` |
| `GROQ_API_KEY` | Key thật bạn đã thêm; chỉ backend đọc |
| `GROQ_MODEL` | Model đang cấu hình: `openai/gpt-oss-20b` |
| `DIABETES_LLM_ENABLED` | `true` để sử dụng Groq; cần kết nối Internet cho các lời gọi LLM |

Backend đọc `DATABASE_URL`; các biến `POSTGRES_*` trong mẫu phục vụ Docker Compose. Máy này đang dùng PostgreSQL Windows Service và Neo4j local. Hướng dẫn chi tiết về URL, password và `.env`: [local_environment_vi.md](docs/local_environment_vi.md).

### Khởi tạo Neo4j lần đầu và nạp kho kiến thức

Trên máy hiện tại, các bước này đã hoàn tất. Khi cần chuẩn bị lại:

```powershell
cd "D:\phát triển ht thông minh\diabetes-mas-final"

python scripts/local_neo4j.py setup
python scripts/local_neo4j.py start

python scripts/prepare_diabetes_corpus.py --fetch
python scripts/prepare_diabetes_embeddings.py --download
python scripts/prepare_diabetes_reranker.py --download
python scripts/seed_diabetes_graph.py

python -m alembic upgrade head
```

Chỉ chạy bước sau khi bước trước thành công. Các lệnh `--fetch` / `--download` cần Internet. Chúng chuẩn bị nguồn và model retrieval; model MLP/Q-policy đã huấn luyện nằm riêng trong `artifacts/models/` và `artifacts/policies/`, cần giữ các artifact này khi chạy hệ thống. Corpus/graph đã lưu bền vững nên không cần nạp lại mỗi lần mở web.

Neo4j trên máy này dùng dữ liệu tại `D:\diabetes-mas-local\neo4j`, binary đã cài tại đường dẫn ASCII và Java 17. Khi dùng máy khác, cung cấp đường dẫn cài đặt thực tế bằng `--home` và `--java-home` theo [hướng dẫn local](docs/local_environment_vi.md).

## 5. Xử lý lỗi thường gặp

| Hiện tượng | Kiểm tra / lệnh xử lý |
|---|---|
| Neo4j Browser báo `Connection refused` | Chạy `python scripts/local_neo4j.py start`, chờ `available`, rồi mở lại cổng 7474. Cần bật lại sau khi Windows khởi động. |
| Neo4j mở trang nhưng đăng nhập thất bại | Dùng `NEO4J_USER` / `NEO4J_PASSWORD` trong `.env`; mật khẩu database không tự đổi khi bạn sửa riêng file `.env`. |
| Web cổng 5173 không mở được | Kiểm tra terminal FE vẫn đang chạy và không báo lỗi. Chạy `npm run dev -- --strictPort` tại thư mục `frontend`. |
| FE mở được nhưng API lỗi / không kết nối BE | Kiểm tra terminal BE và `http://127.0.0.1:8000/health`; giữ backend ở cổng 8000 để khớp Vite proxy. |
| PostgreSQL unavailable / migration lỗi | Kiểm tra service `postgresql-x64-17`, database tồn tại, user/password/port trong `DATABASE_URL`; chạy `python -m alembic upgrade head` sau khi kết nối đúng. |
| Cổng 5173 hoặc 8000 đã bị chiếm | Kiểm tra terminal FE/BE đã mở trước đó; dùng lại tiến trình đang chạy hoặc dừng đúng tiến trình đó trước khi chạy lại. |
| Python báo thiếu module | Chạy bằng Python có đủ dependency; cài extras ở phần 4 vào đúng môi trường đó. |
| Groq unavailable / rate limited | Kiểm tra key/model/Internet/hạn mức và cảnh báo trong kết quả; restart BE sau khi sửa `.env`. Fallback trích đoạn nguồn được ghi rõ trên UI. |

Các lệnh chạy benchmark/test và lịch sử các phase được ghi trong [demo guide](docs/diabetes_expansion_demo.md), [experimental protocol](docs/diabetes_expansion_experiments.md) và phần thu gọn bên dưới. Chúng phục vụ kiểm chứng riêng; bộ test migration cần database test chuyên dụng.

---

## Kiến trúc hiện tại — grounded diabetes research expansion

For this machine's configured PostgreSQL, authenticated Neo4j and Groq, use [the Vietnamese .env/Neo4j guide](docs/local_environment_vi.md). [Actual local-service and live Groq smoke verification](docs/validation/local_environment/report.md) is newer than the historical full offline report; it is not a model-quality benchmark.

The user-authorized expansion adds 14 versioned NIDDK sources, multilingual dense retrieval and cross-encoder reranking on CPU, a Groq structured LLM adapter, separate claim/evidence verification, and a six-agent Coordinator with bounded retrieval/repair feedback. Current frontend uses `/api/v2`, runtime 3.0; historical `/api/v1` runtime 2.4 and frozen DL/RL remain supported. No local LLM training or Phase 08 rollout.

Start with [current demo/setup](docs/diabetes_expansion_demo.md), [source catalog](docs/diabetes_data_catalog.md), [LLM/key and grounding](docs/llm_grounding.md), [evaluation protocol](docs/diabetes_expansion_experiments.md), [actual verification](docs/validation/diabetes_expansion/report.md) and [ADR 0007](docs/decisions/0007-diabetes-grounded-llm-runtime.md). Full check: `python scripts/check_diabetes_expansion.py` with dedicated test services. Bounded real provider evaluation: `python scripts/evaluate_diabetes_llm.py --live --limit 6`.

Missing key is a visible extractive fallback, never claimed as LLM success. Full live conversational verification remains a separate gate; read the current machine report rather than historical phase readiness labels.

<details>
<summary>Tài liệu các phase trước và lệnh kiểm chứng lịch sử</summary>

# Phase 07 — historical local research demo

React/TypeScript/Vite GlucoLab now provides Overview, synthetic Assessment, Knowledge assistant, persisted Execution monitor and measured Experiments. All business outputs use the actual Coordinator API, frozen prediction model, Neo4j evidence, educational RL and two Safety gates. No frontend agent output/metric fixtures. No Phase 08 work.

See [demo setup and scenarios](docs/demo_guide.md), [experimental protocol](docs/experiments.md), [measured verification](docs/validation/phase07/report.md) and [phase status](docs/phase_status.md). Full reproducibility: `python scripts/check_phase07.py` with two dedicated test DB URLs, seeded Neo4j and installed Chromium. Model/policy artifacts remain frozen. Known safe-query overblocking is retained as a benchmark failure, not relabeled as success.

Historical phase setup follows. `scripts/evaluate_rl.py` now writes Phase 07 experiment artifacts while using the unchanged Phase 06 evaluator/policy; the historical exported Phase 06 results remain in their existing directory.

# Phase 06 remediation — historical state

Current runtime 2.4, policy education-q-1.1, Safety policy safety-1.1. The review action-allowlist and evaluation-parity failures have regression checks; Education exposes both proposed and effective action with override reason. Home status text now reflects Phase 06.

```powershell
python scripts/check_phase06.py --execute-notebook
python scripts/verify_phase06_review.py
# From frontend/: npm run build
```

Full verifier requires separate disposable PostgreSQL test URLs and seeded Neo4j as below; it rejects skipped tests. Current logs: docs/validation/phase06_fixes/. Policy 1.1 artifacts under artifacts/policies/education-q-1.1/; previous artifact/report retained as history. New scientific metrics evaluate the same fallback-aware selector used by serving. No clinical claims or Phase 07 implementation. See docs/decisions/0006-phase06-review-fixes.md and docs/rl_experiments.md.

# Phase 06 — offline educational Q-learning and integrated RL agent

```powershell
# From project root after activating .venv:
python -m pip install -e ".[dev,ml,knowledge,rl]"
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/04_rl_q_learning_training.ipynb --ExecutePreprocessor.timeout=600
python scripts/evaluate_rl.py
python -m pytest backend/tests/test_rl_phase06.py -v
```

Training uses only a synthetic education simulator; no clinical/treatment action and no patient health-outcome reward. Outputs: artifacts/policies/education-q-1.0/q_table.npz + manifest.json; experiments/results/phase06 and experiments/figures/phase06. Policy artifacts are locally present but gitignored; train notebook recreates them. No training occurs during API requests.

For full current acceptance, configure the dedicated PostgreSQL/Neo4j test environment documented in earlier phases, then run `python scripts/check_phase06.py --execute-notebook`. This executes the notebook, exported-policy evaluation, full tests and actual API/persistence checks. Without the flag, verifier requires existing successful notebook execution evidence and still evaluates/tests the actual exported artifact. Do not point migration tests at a real app DB.

Main app now integrates real RL. Runtime schema_version=2.3; default simulated knowledge/engagement are medium, explicitly NOT measured user traits. Policy chooses only educational steps; two mandatory Safety gates remain. Missing artifact/out-of-domain/unvisited state uses explicit rule fallback, not random action or silent old policy. See [MDP](docs/rl_mdp.md), [experiment results](docs/rl_experiments.md) and ADR 0005. Earlier documentation below is historical.

# Phase 05 — current safety integration

Current runtime uses schema_version=2.2 and mandatory input/output safety gates. Rule engine safety-1.0 has five groups, 41 synthetic fixture scenarios, explicit veto/escalation/clarification and redacted audit. See [rule catalog](docs/rule_catalog.md), [safety policy and test commands](docs/safety_policy.md).

`python -m pytest backend/tests/test_safety_phase05.py -v` runs standalone engine/workflow safety tests. `python scripts/check_phase05.py` runs full dedicated PostgreSQL/Neo4j verification with actual saved decisions. Clients with explicit 2.1 must update to 2.2; old run snapshots return 409 pending safety review. No diagnosis, prescribing or clinical emergency detection service. Earlier setup/history follows.

# Phase 04 — current MAS knowledge integration

Install `python -m pip install -e ".[dev,ml,knowledge]"`, configure Neo4j environment/.env, then `python scripts/seed_knowledge.py --fetch`. Main workflow still runs through `POST /api/v1/mas/runs` and PostgreSQL. Knowledge/Education now use retrieved NIDDK excerpts and citations; no LLM or RL training.

See [graph setup/provenance](docs/knowledge_graph.md), [retrieval and evaluation](docs/rag_pipeline.md), and `python scripts/check_phase04.py` for dedicated-database verification. Older phase setup follows as history. No clinical diagnosis or prescribing service.

# Phase 03 — current backend

Default app now uses real Phase 02 prediction serving and PostgreSQL. Earlier sections below are historical setup; RAM/stub statements describe earlier phases. No Neo4j/RAG/RL is integrated. Research score only, never clinical diagnosis.

```powershell
# From diabetes-mas-final; activate .venv first
python -m pip install -e ".[dev,ml]"
# Requires Phase 02 artifacts already produced; no training on requests.
python scripts/prepare_serving.py
# Set DATABASE_URL in .env to your local PostgreSQL; never commit credentials.
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/models/current
$body = @{is_synthetic=$true; assessment=@{pregnancies=0; glucose=100; blood_pressure=70; skin_thickness=20; insulin=50; bmi=22; diabetes_pedigree=0.3; age=30}} | ConvertTo-Json -Depth 5
$run = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/mas/runs -ContentType 'application/json' -Body $body
Invoke-RestMethod "http://localhost:8000/api/v1/mas/runs/$($run.run_id)"
Invoke-RestMethod "http://localhost:8000/api/v1/mas/runs/$($run.run_id)/trace"
python scripts/demo_prediction.py
```

Demo requires DATABASE_URL in process environment (not only .env); prints three SYNTHETIC cases with real model output, persisted UUID and trace; saves docs/validation/phase03/demo.json. Do not use real patient information. Snapshot survives application restart when same PostgreSQL is configured. No auth; local course demo only.

Testing uses two separate disposable databases; migration regression performs downgrade, so do not target a real app database:

```powershell
$env:PHASE02_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_phase02_test'
$env:PHASE03_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_phase03_test'
python scripts/check_phase03.py
```

Verifier requires both URLs, rejects skipped tests, runs tests/demo and real Uvicorn HTTP readback in a new process. Logs live under docs/validation/phase03/. Older check_phase01.py targets historical app behavior; use check_phase03.py for current acceptance. Model_DEVICE defaults cpu; MODEL_DEVICE=cuda explicitly requests CUDA and returns unavailable if unsupported (no silent device/model substitution). Missing/corrupt artifacts require repair and app restart because failed lazy loads are cached.

Contracts: RunInput/runtime 2.1, PredictionResult serving 1.1, unchanged AssessmentInput v1. Explicit 2.0 payloads need migration. See [ADR 0003](docs/decisions/0003-serving-persistence.md) and [agent contracts](docs/agent_contracts.md) for range/zero handling and transaction semantics. Artifact paths remain artifacts/models/pima-mlp-0.2.0/, including serving.json with train-only bounds; checksums protect trained artifacts, not authenticity. No fitting/retraining occurs in backend serving. Existing data/model cards remain research limitations.

---

## Earlier phase documentation

# Diabetes Multi-Agent Intelligent Support System

Đồ án cá nhân môn Phát triển các hệ thống thông minh. Phase 01 bổ sung runtime MAS trên nền Phase 00; hệ thống hỗ trợ đánh giá nguy cơ và giáo dục về tiểu đường. Chưa tích hợp model, Neo4j/RAG hoặc policy RL; Education chỉ abstain và Safety chỉ có rules tối thiểu.

## Windows / PowerShell

Yêu cầu Python 3.11+, Node.js 22.12+ (hoặc 20.19+), npm. Docker Desktop chỉ cần khi thử PostgreSQL. Chạy từ thư mục `diabetes-mas-final`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Sửa .env: thay REPLACE_USER, REPLACE_PASSWORD bằng thông tin local.
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Nếu PowerShell chặn activate, dùng trực tiếp `.\.venv\Scripts\python.exe` thay `python`; không cần đổi execution policy của máy. Backend không kết nối DB lúc khởi động.

Terminal khác, từ project root:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/api/v1/system/capabilities
python -m pytest -q
python scripts/verify_phase00.py
# Chạy tất cả checks và lưu log (cần npm dependencies đã cài):
python scripts/run_checks.py
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
# http://localhost:5173
# Build production:
npm run build
```

Frontend mặc định gọi `http://localhost:8000`. Có thể tạo `frontend/.env.local` với `VITE_API_BASE_URL=http://localhost:8000`. Không đặt secret trong biến VITE: chúng công khai trong bundle. `CORS_ORIGINS` ở .env backend là JSON array các origin cho phép. Khởi động lại backend khi sửa environment.

## PostgreSQL / Alembic skeleton

```powershell
# Từ project root, sau khi sửa .env:
docker compose --env-file .env -f infra/docker/compose.yaml up -d postgres
python -m alembic heads
# Chỉ dùng sau khi kết nối DB và có migration được phê duyệt ở phase sau:
# python -m alembic upgrade head
```

Chưa có business table hay revision. `heads` trống là đúng cho skeleton. `DATABASE_URL` dùng driver `postgresql+psycopg`; percent-encode ký tự đặc biệt trong credentials của URL. Compose chỉ mở DB trên loopback và lưu volume. Không tự xóa volume.

Dependency cho phase sau được khai báo optional, chưa cài/chưa tích hợp:

```powershell
# Khi phase tương ứng được giao:
# python -m pip install -e ".[ml,knowledge]"
```

## Phase 01 — API và demo

```powershell
# Từ project root, sau khi cài .[dev]:
python -m pytest backend/tests -v
python scripts/demo_mas.py
python scripts/check_phase01.py
# Backend đang chạy: tạo question-only run
$body = @{question="What is diabetes?"} | ConvertTo-Json
$run = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/mas/runs -ContentType 'application/json' -Body $body
Invoke-RestMethod "http://localhost:8000/api/v1/mas/runs/$($run.run_id)"
Invoke-RestMethod "http://localhost:8000/api/v1/mas/runs/$($run.run_id)/trace"
Invoke-RestMethod http://localhost:8000/api/v1/mas/agents
```

POST chạy đến terminal và trả 201 cùng run_id, status, agent_results, response, evidence, agent_trace, warnings, limitations. Input dùng schema_version=2.0 (mặc định), assessment 8 Pima field theo v1.0 và/hoặc question. JSON assessment thiếu feature bị từ chối; không tính score khi chưa có model.

Demo có ba case SYNTHETIC: câu hỏi giáo dục (DEGRADED), assessment chưa model (DEGRADED), yêu cầu liều insulin (BLOCKED). Log/JSON thực tế ở `docs/validation/phase01/`. Các file validation Phase 00 được giữ làm lịch sử; `check_phase01.py` dùng thư mục log riêng.

## Phạm vi thực tế

- `/health`: application liveness; không khẳng định DB/model/tool sẵn sàng.
- `/api/v1/system/capabilities`: Coordinator/Education/Safety có runtime thật trong giới hạn; Prediction/Knowledge/RL là stub. Rules chỉ tối thiểu.
- `/api/v1/mas/runs`: orchestration tuần tự thực sự, điều phối có điều kiện, timeout, fallback, trace và safety gate.
- Runtime contracts v2.0 bổ sung, v1.0 được giữ nguyên; xem ADR 0002. Scaffold cũ chuyển sang mas/legacy.py.
- Run repository trong RAM, capacity 100, eviction run cũ nhất; restart hoặc chạy worker khác sẽ không thấy run. Không lưu request, không có persistent storage (Phase 03 chưa triển khai).
- Education không tạo giải thích y khoa khi thiếu tri thức, không tạo citation/prediction giả. Không tự tính nguy cơ từ assessment. Safety là lexical rule gate có thể bỏ sót/chặn nhầm, chưa phải full rule engine (Phase 05).
- Chỉ chạy local với dữ liệu synthetic; chưa auth, chưa dùng cho bệnh nhân thật hoặc quyết định y khoa. Chưa kiểm chứng PostgreSQL/Docker/ML/Neo4j runtime.

Xem [kiến trúc](docs/architecture.md), [MAS workflow](docs/mas_workflow.md), [contracts](docs/agent_contracts.md), [trạng thái phase](docs/phase_status.md), [traceability](docs/requirements_traceability.md).


## Phase 02 — offline research pipeline

Ba notebook EDA/split, MLP training và held-out evaluation đã được bổ sung. Xem [lệnh tái lập](docs/phase02_reproduce.md), [data card](docs/data_card.md), [model card](docs/model_card.md). Coordinator và Prediction Agent chưa tích hợp checkpoint; giữ runtime Phase 01. Trạng thái và bằng chứng Phase 02 nằm trong docs/validation/phase02/.

</details>
