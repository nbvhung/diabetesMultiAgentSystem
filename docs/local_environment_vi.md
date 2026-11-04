# Hoàn thiện .env và sử dụng Neo4j local

Chạy lệnh trong thư mục `diabetes-mas-final`. Backend đọc file `.env` tại thư mục hiện hành. Không đưa file này vào Git hoặc gửi API key/mật khẩu trong chat.

## Các thành phần dùng để làm gì?

| Thành phần | Vai trò trong dự án |
|---|---|
| PostgreSQL | Lưu synthetic assessment, prediction, workflow run và trace |
| Neo4j | Lưu các đoạn evidence, nguồn và quan hệ kiến thức diabetes |
| Groq | Chạy LLM từ xa để soạn câu trả lời và kiểm tra claim theo evidence |

Neo4j và Groq là hai dịch vụ khác nhau. Tạo API key Groq không tự tạo database Neo4j. Dự án hiện dùng Neo4j Community chạy trên máy, không yêu cầu tài khoản Neo4j cloud.

## PostgreSQL: bạn điền thông tin của mình

Backend dùng trực tiếp `DATABASE_URL`. Ví dụ định dạng:

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@127.0.0.1:5432/diabetes_mas
```

Thay user/password/port/tên database theo PostgreSQL của bạn. Database phải tồn tại. Nếu password chứa ký tự đặc biệt như `@`, `#`, `/`, hãy mã hóa phần password theo URL, ví dụ `@` thành `%40`. Các biến `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` trong mẫu phục vụ Docker Compose; chỉ sửa chúng sẽ không thay thế `DATABASE_URL` mà backend sử dụng.

Sau khi PostgreSQL chạy và URL đúng:

```powershell
python -m alembic upgrade head
```

## Neo4j: đã được cấu hình riêng cho dự án

Script `scripts/local_neo4j.py` dùng Neo4j Community 5.26 đã có trên máy và Java 17. Instance mới tách biệt với graph test dùng ở các phase trước. Thư mục dữ liệu/config/log là `D:\diabetes-mas-local\neo4j`; `.env` vẫn ở thư mục dự án.

Đường dẫn dữ liệu chỉ có ký tự ASCII để tránh lỗi launcher Java/Neo4j trên Windows khi workspace chứa dấu tiếng Việt. Script ghi Unicode escape chuẩn cho Java Properties khi cần. Đây là cài đặt local dành cho nghiên cứu, chỉ lắng nghe `127.0.0.1`.

Trong `.env`, các giá trị kết nối đã được điền:

```dotenv
NEO4J_URI='bolt://127.0.0.1:7687'
NEO4J_USER='neo4j'
# NEO4J_PASSWORD đã có giá trị thật trong .env. Giữ nguyên giá trị đó.
```

Không thay mật khẩu bằng dòng mẫu. Chỉ đổi password trong `.env` không tự đổi password của database đã khởi tạo.

Các lệnh quản lý từ thư mục dự án:

```powershell
# Khởi tạo lần đầu; không reset mật khẩu của database đã khởi tạo.
python scripts/local_neo4j.py setup

# Chạy nền và kiểm tra bằng đăng nhập thật.
python scripts/local_neo4j.py start
python scripts/local_neo4j.py status

# Dừng riêng các JVM mang marker sở hữu của instance dự án.
python scripts/local_neo4j.py stop
```

`start` không chiếm cổng của dịch vụ khác. Bật máy lại thì chạy `start`; hiện không cài Windows Service tự khởi động. Trên Windows, script thử stop chính thức trước, rồi chỉ kết thúc JVM có marker riêng nếu console deployment không hỗ trợ graceful stop. Không dùng thao tác này để thay thế quy trình vận hành một database production.

Nếu cài đặt bị chuyển sang máy/đường dẫn khác, truyền `--home` tới thư mục Neo4j 5.26 đã giải nén tại đường dẫn ASCII và `--java-home` tới JDK 17. Binary đang dùng được ghi trong `D:\diabetes-mas-local\neo4j\initialized.json`; không xóa thư mục cài đặt đó khi còn sử dụng instance.

## Mở Neo4j Browser để xem graph

Nếu trình duyệt báo **Connection refused / Không thể truy cập**, hãy bật instance trước. Sau mỗi lần khởi động lại Windows, nhấp đúp `start_neo4j.cmd` ở thư mục dự án, hoặc chạy:

```powershell
cd "D:\phát triển ht thông minh\diabetes-mas-final"
python scripts/local_neo4j.py start
python scripts/local_neo4j.py status
```

Chờ script báo `status: available` rồi mở Browser. `start` thường cần khoảng 15–30 giây khi instance đang tắt. Cài đặt hiện tại được bật thủ công sau khi Windows khởi động; chưa đăng ký Windows Service tự chạy.

Mở `http://127.0.0.1:7474/browser/`. Đăng nhập với:

- Connection URI: `bolt://127.0.0.1:7687`.
- Username: `neo4j`.
- Password: đọc giá trị `NEO4J_PASSWORD` trong `.env`, không bao gồm hai dấu nháy bao ngoài.
- Database: `neo4j` nếu giao diện hỏi.

Cổng 7474 là giao diện trình duyệt; cổng 7687 là kết nối Bolt của Python backend. Không điền địa chỉ HTTP Browser vào `NEO4J_URI`.

Nạp graph từ các nguồn đã chuẩn bị trên máy:

```powershell
python scripts/seed_diabetes_graph.py
```

Lệnh có thể chạy lại: dùng MERGE và kiểm tra idempotence; không tải evidence mới hoặc tạo nội dung y khoa giả. Corpus hiện tại có 449 đoạn, 14 nguồn NIDDK và 11 assertion có câu dẫn chứng. Nếu máy mới chưa có corpus/model retrieval, làm bước prepare trong `diabetes_expansion_demo.md` trước.

Dán câu lệnh Cypher sau vào ô lệnh Browser để kiểm tra:

```cypher
MATCH (e:DiabetesEvidence)
RETURN count(e) AS evidence_chunks;
```

Xem quan hệ kiến thức dưới dạng đồ thị:

```cypher
MATCH p=(s:DiabetesConcept)-[:HAS_RISK_FACTOR|HAS_SYMPTOM|SCREENED_WITH|HAS_COMPLICATION]->(o:DiabetesConcept)
RETURN p LIMIT 30;
```

Các cạnh là quan hệ giáo dục được dự án tuyển chọn và ràng buộc nguồn, không phải kết luận rút ra từ hồ sơ của bạn.

## Groq và chạy ứng dụng

Giữ nguyên key thật bạn đã thêm. Cấu hình hiện dùng:

```dotenv
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TIMEOUT_SECONDS=25
DIABETES_LLM_ENABLED=true
```

Sau khi PostgreSQL đã migrate và Neo4j đang chạy:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Terminal khác:

```powershell
cd frontend
npm run dev -- --strictPort
```

Mở `http://127.0.0.1:5173` và kiểm tra Overview. Backend phải được khởi động lại sau khi sửa `.env`. Dùng dữ liệu SYNTHETIC cho assessment và demo.

Tài liệu chính thức: [cổng và connector Neo4j](https://neo4j.com/docs/operations-manual/5/configuration/connectors/), [đặt mật khẩu ban đầu](https://neo4j.com/docs/operations-manual/5/configuration/set-initial-password/), [Java tương thích Neo4j 5.26](https://neo4j.com/docs/operations-manual/5/installation/requirements/).
