# Triển khai demo — Phase 08

Hai hình thức được tách rõ. **Native + HTTPS tạm đã chạy thật**; **Docker runtime và cloud hosting chưa hoàn thành**. Không gọi Quick Tunnel là ứng dụng chạy độc lập trên cloud.

## Demo HTTPS đang kiểm chứng

URL đã kiểm chứng: **https://champion-sonic-dept-charged.trycloudflare.com**. Username: `demo`; mật khẩu ở file ignored `.env.demo`, biến `DEMO_ACCESS_PASSWORD`. Không đưa mật khẩu vào báo cáo, source hoặc ảnh chụp. URL có thể hết hạn sau khi tunnel/máy dừng; kiểm tra lại trước buổi bảo vệ.

```powershell
# PostgreSQL + Neo4j + BE phải đang chạy; .env có key của bạn.
npm --prefix frontend run build
python scripts/demo_host.py start --tunnel
python scripts/demo_host.py status
# Khi kết thúc demo:
python scripts/demo_host.py stop
```

Nếu đã có demo đang chạy thì dùng `status`; script không tạo tiến trình trùng. Khi dừng chỉ terminate đúng PID/command của gateway và tunnel do script sở hữu, giữ BE/DB nguyên vẹn. Nếu URL cũ đã tắt: start lại sẽ được URL mới. Cài `cloudflared` từ [nguồn Cloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) hoặc đặt binary đã kiểm tra SHA256 trong `.tools/phase08/cloudflared.exe`.

Gateway `backend/app/demo_gateway.py` bind `127.0.0.1:8082`, phục vụ `frontend/dist`, proxy cùng origin tới `127.0.0.1:8000`; cổng duy nhất tunnel thấy là gateway. Basic authentication kiểm tra phía server, giới hạn 6 POST workflow/phút, payload tối đa 16 KiB, API allowlist, không chuyển Authorization của demo về API, CSP và no-store cho API. Gateway không đọc Groq/DB secrets. Đây là lớp giới hạn demo, không phải hệ thống IAM/production hardening đầy đủ. Khi dùng tunnel, Basic auth được gửi qua HTTPS; không chia sẻ cổng HTTP local trên mạng ngoài.

[Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) tạo URL tạm và không có cam kết uptime. Máy phải bật, internet phải hoạt động, PostgreSQL/Neo4j/BE/gateway/tunnel phải còn chạy. Đường truyền tới Groq có thể lỗi; UI sẽ ghi extractive hoặc unavailable đúng thực tế. Tải model trước và mở readiness một lần để tránh cold start ngay lúc demo.

## Docker Compose

Canonical file: `compose.yaml`; Dockerfiles ở `infra/docker`. Cấu hình cũ `infra/docker/compose.yaml` chỉ phục vụ PostgreSQL lịch sử, không phải cấu hình triển khai toàn hệ thống.

```powershell
python scripts/setup_compose_env.py
# Thêm key vào .env.compose, không sửa file nếu đã tồn tại.
docker compose --env-file .env.compose config --quiet
docker compose --env-file .env.compose up --build --wait
docker compose --env-file .env.compose ps
docker compose --env-file .env.compose logs initialize backend
# Dừng nhưng giữ data:
docker compose --env-file .env.compose down
```

Không dùng `down -v` nếu cần giữ dữ liệu. PostgreSQL và Neo4j dùng named volumes. Khởi động theo dependency: database healthy → initialize hoàn thành → backend healthy → frontend. Thiết kế theo [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/); health là điều kiện sẵn sàng, không chỉ thứ tự tạo container. `/health` là liveness; kiểm tra `/api/v2/system/readiness` và workflow riêng để xác nhận nghiệp vụ.

Backend image dùng Python 3.11, PyTorch CPU, user không phải root; không chứa `.env` hoặc checkpoint trong layer. Frontend multi-stage `npm ci`/Vite → nginx, API cùng origin, timeout đủ cho Coordinator. Ba bind mount read-only cung cấp artifacts, public corpus và experiment bundles. Initialize fail nếu thiếu model/policy/encoder/reranker; không “khởi động xanh” bằng output giả. Groq key rỗng vẫn có fallback minh bạch, nhưng không đủ để tuyên bố LLM demo thành công.

Profile xem DB trên host, dùng port khác native:

```powershell
docker compose --env-file .env.compose -f compose.yaml -f infra/docker/compose.dev.yaml up --build --wait
```

PostgreSQL 55433; Neo4j Browser 17475/Bolt 17688; API 18080. Các cổng bind loopback. Không publish trực tiếp database; để tunnel đi qua gateway có kiểm soát. Nếu muốn dùng gateway với nginx Compose, đổi `DEMO_UPSTREAM` trong `.env.demo` thành `http://127.0.0.1:8080`; gateway tiếp tục phục vụ static build và chuyển API qua nginx.

## Trạng thái chạy thật và phần cần đóng

Ngày 03/11/2026: Compose CLI v5.7.0 tải từ release chính thức, SHA256 khớp metadata GitHub. `config --quiet` thành công. `up --build --wait` thất bại vì không có Docker engine: `open //./pipe/docker_engine: The system cannot find the file specified`. Không có WSL trên host. Vì vậy image build, Linux wheel compatibility, Neo4j image healthcheck, startup/restart/volume survival trong container **chưa được xác minh**; không đánh dấu PASS dựa trên native tests.

Trên máy có Docker: chạy đầy đủ lệnh trên, xác minh initialize exit 0 và bốn service healthy; chạy ba scenario, restart backend/graph và đọc lại run; down/up không xóa volume rồi kiểm tra persistence. Ghi image digests, resource usage và log thực. Các image hiện dùng version tags, chưa phải digest lock được build/test. Đây là gate còn lại trước READY_FOR_DEFENSE theo acceptance nghiêm ngặt.

## Cloud hosting

**NOT_COMPLETED**. Chưa có VPS, tài khoản hosting, DNS hoặc credentials được cấp. Để triển khai độc lập, dùng Linux VPS chạy Compose, volume backup, HTTPS reverse proxy và auth; ước lượng ban đầu cần kiểm thử trên host có khoảng 6–8 GB RAM, không phải cam kết cấu hình tối thiểu. Chỉ tuyên bố cloud deployment sau khi có URL thật, HTTPS/auth và workflow xuyên suốt được kiểm tra từ bên ngoài. Không dùng frontend static hosting riêng như bằng chứng đã deploy backend + PostgreSQL + Neo4j.
