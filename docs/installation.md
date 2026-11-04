# Cài đặt và tái lập từ source mới

Đọc [audit yêu cầu](phase08_scope_audit.md) và [trạng thái thực tế](phase_status.md) trước. Các lệnh chạy tại thư mục gốc chứa `pyproject.toml` và `compose.yaml`. Nếu đã có repository do nhóm cung cấp thì clone repository đó; hiện workspace không có Git remote nên tài liệu không đưa URL clone giả. Không cần train lại khi sử dụng đúng checkpoint và corpus đã xác minh của bản demo.

## 1. Dependencies

Yêu cầu: Python 3.11, Node 22, PostgreSQL 16/17, Neo4j 5.26; Docker Engine + Compose để chạy cấu hình container. Windows cần Docker Desktop với Linux containers/WSL2 hoặc một Docker host Linux. Máy kiểm chứng hiện **chưa có Docker Engine/WSL**, vì vậy phần container chưa được thực thi. Dành ít nhất khoảng 6 GB RAM khả dụng cho graph, hai model retrieval và runtime; đây là mức dự phòng cấu hình, không phải benchmark RAM tối thiểu đã đo.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0
python -m pip install -r infra/docker/runtime-requirements.txt
python -m pip install -e ".[dev,ml,knowledge,rl,semantic]"
npm --prefix frontend ci
```

`runtime-requirements.txt` khóa các dependency trực tiếp theo môi trường native đã chạy, không phải toàn bộ dependency bắc cầu hay một Linux image đã kiểm chứng. `package-lock.json` khóa frontend. Ghi lại `pip freeze`, image digest và platform khi hoàn thành kiểm chứng Docker trên host khác.

## 2. Environment

```powershell
Copy-Item .env.example .env
```

Chỉ làm lệnh copy khi chưa có `.env`. Sửa `DATABASE_URL`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `GROQ_API_KEY`. Giữ `.env` ngoài Git. Groq dùng inference API, **không cần train LLM**. Native environment dùng host `127.0.0.1`; container dùng tên service. `DIABETES_LLM_ENABLED=false` là chế độ dự phòng có ghi nhãn extractive, không phải lời đáp LLM thật.

## 3. Chuẩn bị dữ liệu Pima

```powershell
python scripts/download_pima.py
```

Downloader kiểm tra SHA256 trước khi ghi `data/raw/pima.csv`. Pima là dữ liệu nghiên cứu lịch sử có thật, không phải synthetic. Quyền tái phân phối chưa được xác minh; xem [data card](data_card.md). Không thay bằng dữ liệu tự sinh khi download thất bại.

## 4–5. Train DL và Q-learning, hoặc dùng checkpoint đã lưu

Nếu nhận artifact đáng tin của bản demo, đặt đúng cấu trúc `artifacts/models/pima-mlp-0.2.0`, `artifacts/policies/education-q-1.1`; loaders sẽ kiểm tra manifest. Các thư mục này đang gitignored; clone source đơn thuần không tự có checkpoint. Không load file joblib từ nguồn không tin cậy.

Handoff local đã có `.tools/exports/diabetes-demo-artifacts.zip` khoảng 984 MB và manifest SHA256, gồm cả retrieval weights/corpus/experiments. Copy archive cùng source, kiểm SHA256 với manifest rồi giải nén **chỉ vào checkout mới/rỗng**, không đè bản frozen đang dùng:

```powershell
Get-FileHash .tools/exports/diabetes-demo-artifacts.zip -Algorithm SHA256
python -m zipfile -e .tools/exports/diabetes-demo-artifacts.zip .
```

Archive không chứa raw Pima, env hoặc DB dumps. Không tự upload/share public; quyền tái phân phối Pima-derived checkpoint cần review. Nếu đã restore đầy đủ, bỏ qua train/download lại weights; loaders và seed sẽ kiểm chứng dữ liệu có sẵn. Có thể kiểm tất cả file trong `demo_artifacts_manifest.json` sau restore, không chỉ archive hash.

Nếu chưa có artifact, chạy trên bản sao nghiên cứu để không ghi đè checkpoint frozen của demo:

```powershell
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_diabetes_eda_and_split.ipynb --ExecutePreprocessor.timeout=600
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_diabetes_dl_training.ipynb --ExecutePreprocessor.timeout=600
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/03_diabetes_model_evaluation.ipynb --ExecutePreprocessor.timeout=600
python scripts/prepare_serving.py
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/04_rl_q_learning_training.ipynb --ExecutePreprocessor.timeout=1200
```

Notebook 01 fit preprocessing trên train và tạo split; 02 train MLP; 03 đánh giá cùng baseline; 04 train/evaluate/export Q-policy bằng simulator. Không train trong API requests. Seed, checkpoint và báo cáo mới có thể khác do dependency/platform; không gắn lại các metric lịch sử cho lần train mới.

## 6. PostgreSQL schema

Tạo database rỗng bằng công cụ PostgreSQL và cấu hình URL. Sau đó:

```powershell
python -m alembic upgrade head
python -m alembic current
```

Head: `0002_phase03`; không downgrade database demo. Hai database test phải khác database ứng dụng và khác nhau vì migration test có downgrade/drop schema.

## 7. Corpus, retrieval models và Neo4j

```powershell
python scripts/prepare_diabetes_corpus.py --fetch
python scripts/prepare_diabetes_embeddings.py --download
python scripts/prepare_diabetes_reranker.py --download
python scripts/seed_diabetes_graph.py
```

Tải nguồn và model là bước chuẩn bị có chủ ý; inference không tải tự động. Nếu đã có snapshot/manifest/weights của demo thì bỏ `--fetch`/`--download` và giữ nguyên corpus release. Fetch web mới có thể đổi snapshot hoặc cần rà layout; không dùng số liệu cũ như phép đo trên snapshot mới. Native Neo4j hiện có hướng dẫn riêng ở [local_environment_vi.md](local_environment_vi.md).

## 8. Docker Compose

```powershell
python scripts/setup_compose_env.py
# Mở .env.compose và thêm GROQ_API_KEY; không copy credentials thật vào source.
docker compose --env-file .env.compose config --quiet
docker compose --env-file .env.compose up --build --wait
docker compose --env-file .env.compose ps
```

Không chạy `setup_compose_env.py` lần nữa nếu file đã có; script chủ động không ghi đè. Artifacts, corpus và kết quả phải có trên host trước `up`. Initialize job migrate, kiểm tra loaders và seed graph; backend chỉ chạy khi job hoàn thành. Chỉ frontend được bind loopback 8080; DB không mở ra internet. Xem [deployment](deployment.md) cho trạng thái kiểm chứng và profile dev.

## 9–10. Kiểm tra API và mở frontend

```powershell
Invoke-RestMethod http://localhost:8080/api/v2/system/readiness
```

Mở `http://localhost:8080`. Với native, chạy BE `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`, FE `npm --prefix frontend run dev`; mở `http://localhost:5173`. Liveness `/health` không chứng minh model/graph sẵn sàng; đọc readiness từng component. Groq chỉ thành `available` sau lời gọi thành công.

## 11. Demo

Theo [demo guide](demo_guide.md): assessment synthetic + risk factors → trace; yêu cầu đổi insulin → veto; câu hỏi thiếu nguồn → clarification. Dùng [script 2 phút](defense/demo_2_minutes.md) khi thời gian bảo vệ ngắn. Có HTTPS tạm qua `python scripts/demo_host.py start --tunnel` sau build và backend khởi động, xem [deployment](deployment.md).

## 12. Tests và evaluation

Checker cuối: `python scripts/check_phase08.py --test-env .env.phase08-test`. File env test phải dùng **hai PostgreSQL database riêng và Neo4j instance riêng**; không copy nguyên URL ứng dụng sang test. Checker kiểm tra các URL này, migrate workflow DB, initialize/seed, chạy backend/frontend/browser, kiểm artifact và thử Compose. Chromium có thể chỉ định bằng `PHASE07_CHROMIUM_PATH`. Các QA HTTP server dùng 18000/18001 và Vite 15173, không thay server demo 8000/5173.

```text
PHASE02_TEST_DATABASE_URL=postgresql+psycopg://REPLACE_USER:REPLACE_PASSWORD@127.0.0.1:REPLACE_TEST_PORT/phase08_migration
PHASE03_TEST_DATABASE_URL=postgresql+psycopg://REPLACE_USER:REPLACE_PASSWORD@127.0.0.1:REPLACE_TEST_PORT/phase08_workflow
NEO4J_TEST_URI=bolt://127.0.0.1:REPLACE_TEST_BOLT_PORT
NEO4J_USER=REPLACE_TEST_USER
NEO4J_PASSWORD=REPLACE_TEST_PASSWORD
```

Không dùng placeholder nguyên trạng. Tạo hai database bằng PostgreSQL tools và một Neo4j database instance test trước. Khi test thủ công, ánh xạ `DATABASE_URL` sang workflow test URL và `NEO4J_URI` sang test URI trong **process test**, không sửa file `.env` ứng dụng. Có thể chọn `--stages backend frontend browser integrity` để chạy chỉ checks phần mềm; việc bỏ Compose không đóng gate triển khai. Checker đầy đủ hiện exit 1 với status BLOCKED do thiếu Docker engine, trong khi backend/frontend/browser đều exit 0.

```powershell
python -m pytest backend/tests -q
npm --prefix frontend test
npm --prefix frontend run build
python scripts/evaluate_prediction.py
python scripts/evaluate_diabetes_rag.py
python scripts/evaluate_diabetes_mas.py
python scripts/evaluate_rl.py
python scripts/evaluate_diabetes_safety.py
python scripts/evaluate_diabetes_llm.py --live --limit 6
```

Full backend integration cần `PHASE02_TEST_DATABASE_URL`, `PHASE03_TEST_DATABASE_URL`, `NEO4J_TEST_URI` trỏ vào service dùng riêng. Thiếu chúng sẽ có skip: không gọi đó là nghiệm thu toàn bộ. Migrate test workflow DB trước khi chạy; bảo đảm `GROQ_API_KEY` rỗng trong test process nhưng `DIABETES_LLM_ENABLED=true` để fake transport unit tests kiểm tra được đường LLM mà không gọi thật. Browser regression dùng provider disabled và fault API riêng. Live benchmark là bước riêng có chi phí/quota; không chạy lại mỗi lần mở demo. Xem [verification Phase 08](validation/phase08/report.md).
