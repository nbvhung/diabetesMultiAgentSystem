# Chuẩn bị Tiểu luận Final V2 và Project01 V2 — 06/11/2026

## Căn cứ và cách hiểu yêu cầu

Đã đọc hai ảnh bảng và `../examination_50_questions_v2.pdf` (13 trang, 51 câu dù tiêu đề ghi 50). Ảnh yêu cầu: nguồn web/PDF → Knowledge Graph/Neo4j → tệp `kb_diabetes.cypher`; KB + RAG để chat; hệ đa agent diabetes tích hợp DL, luật và tri thức. Khi báo cáo phải **show KB Neo4j**, giải thích **RAG nối KB thế nào**, trình bày kiến trúc và chạy demo thực tế. Nguồn Vinmec trên bảng là ví dụ nhìn thấy trong ảnh; không đủ căn cứ kết luận bắt buộc thay NIDDK bằng Vinmec hoặc phải có đồng thời web và PDF.

Ảnh ghi hai đầu mục `tieuluanFinal_Vx` và `Project_Vx`, cùng bốn tỷ lệ 10%, 20%, 30%, 40%. Nhãn ứng với bốn tỷ lệ không đủ rõ để gán chắc cho từng bài. Không tự tính điểm hay cam kết điểm. PDF có bảng **đánh giá vấn đáp riêng**, không tự coi đây là thang điểm của từng báo cáo:

| Thành phần vấn đáp trong PDF | Trọng số |
|---|---:|
| ML/DL | 15% |
| CNN/RNN/LSTM | 10% |
| KG/Neo4j/RAG | 15% |
| Agent/MAS | 15% |
| Kiến trúc và triển khai | 20% |
| Demo và bảo vệ | 15% |
| Tư duy phản biện | 10% |

## Audit trước khi bổ sung

Hệ thống thực có MLP Pima, PostgreSQL, corpus NIDDK 14 nguồn/449 đoạn, semantic encoder, reranker, 11 assertion có trích dẫn, Coordinator cùng Prediction/Knowledge/RL/Education/Verifier/Safety. API `/api/v2/knowledge/graph` đã tồn tại nhưng chưa có màn KB trong web và chưa có tệp Cypher bàn giao độc lập. Không cần xây lại MAS hoặc huấn luyện lại để đáp ứng phần bổ sung trên bảng.

Corpus graph gồm `DiabetesSource`, `DiabetesEvidence`, `DiabetesTopic`, `DiabetesConcept`, `DiabetesAssertion`. Quan hệ miền: `HAS_RISK_FACTOR`, `HAS_SYMPTOM`, `SCREENED_WITH`, `HAS_COMPLICATION`; quan hệ provenance: `HAS_CHUNK`, `SUPPORTED_BY`, `SUBJECT_OF`, `OBJECT`. Assertion chỉ được nhận khi trích dẫn chính xác có trong đoạn của đúng nguồn và mục. Đây là tuyển chọn có luật, không phải LLM tự trích xuất tri thức tùy ý.

## Bổ sung code của V2

- `kb_diabetes.cypher`: toàn bộ KB của đúng corpus runtime, có 5 constraint và 460 câu DML, không APOC/secret/bệnh án. Có thể import lại cùng release. Đây là **script tái dựng property graph**, không phải DB dump hoặc bản sao model/vector index.
- `kb_diabetes.manifest.json`: SHA256, release, số nguồn/đoạn/assertion. `python scripts/export_diabetes_kb.py` tái tạo từ corpus được kiểm checksum; thiếu/corrupt corpus sẽ lỗi, không xuất dữ liệu mẫu thay thế.
- `kb_diabetes_queries.cypher`: truy vấn triples, đồ thị, nhiều bước tới nguồn, số lượng theo release, kiểm assertion thiếu bằng chứng.
- Trang **Đồ thị tri thức** trong web: gọi Neo4j qua API thật, lọc subject/predicate/object, mở quote, passage, evidence ID và link nguồn. Đây là màn bộ ba và provenance; muốn xem node-link dùng Neo4j Browser với câu Graph view trong tệp truy vấn.
- `python scripts/check_report_v2.py --live`: chạy chính DML của exporter hai lần trong một transaction, kiểm mọi thuộc tính evidence/assertion và số cạnh, rồi rollback. Đây là kiểm tra import/readback thực, giữ nguyên DB. Năm constraint được kiểm khi import vào DB mới theo hướng dẫn dưới; script live không kiểm tạo constraint trong DB trống.

## Cách demo có thể bảo vệ được

```powershell
python scripts/start_final_demo.py start
python scripts/export_diabetes_kb.py
python scripts/check_report_v2.py --live
```

Web `http://127.0.0.1:8082`, user `demo`, password trong `.env.demo`. Nếu demo đã chạy thì mở web; frontend mới đã build cần refresh. Mở **Đồ thị tri thức**, lọc `HAS_SYMPTOM`, mở một passage để đối chiếu nguồn. Mở Neo4j Browser `http://127.0.0.1:7474/browser/`, đăng nhập bằng thông tin trong `.env`, chạy từng truy vấn trong `kb_diabetes_queries.cypher`, chọn tab Graph để thấy chuỗi concept → assertion → evidence ← source.

Để thầy tái tạo trên Neo4j mới: đặt `NEO4J_USERNAME`/`NEO4J_PASSWORD` trong môi trường cục bộ, chạy `cypher-shell -a bolt://localhost:7687 -f kb_diabetes.cypher`. Không thêm mật khẩu vào báo cáo hay lệnh chụp màn hình. Cypher không chứa `:use`, nên database đích theo cấu hình cypher-shell. Dùng DB mới để đối chiếu chính xác số lượng; các release cũ trong DB đang dùng được giữ để audit.

Tiếp theo vào **Hỏi về tiểu đường**: hỏi “Bệnh tiểu đường có những triệu chứng nào?”, mở citations rồi **Hành trình agent**. Cho thấy Knowledge tìm evidence từ cùng corpus/Neo4j, Education tạo câu trả lời, Verifier kiểm chứng, Safety quyết định công bố. Nếu provider lỗi, chỉ nhận chế độ fallback/clarification có nhãn. Không báo fallback là gọi LLM thành công.

Để giải thích RAG ↔ KB bằng API, dùng POST `/api/v2/knowledge/search` với body `{"question":"Bệnh tiểu đường có những triệu chứng nào?","strategy":"graph","k":3}`, rồi thử `lexical`, `semantic`, `hybrid` cùng câu hỏi. `graph` dùng topic → evidence trong Neo4j; không giả định mọi retrieval đều traversal assertion nhiều bước. Semantic dùng encoder, hybrid kết hợp candidate/ranking và reranker. Các assertion phục vụ giải thích tri thức/provenance; chưa phải suy luận lâm sàng bằng chuỗi quan hệ. Xem `backend/app/research/retrieval.py` để bảo vệ đúng code.

Cuối cùng chạy Assessment với mẫu **SYNTHETIC**: Prediction gọi checkpoint thật; quan sát score và trace. Thử câu đổi liều insulin để xem Safety veto. Chưa có agent chuyên khoa như trong phác họa bảng; các vai trò hiện tại phân theo nhiệm vụ. Không gắn tên “chẩn đoán” cho model dự báo nguy cơ.

## Nguyên liệu viết hai quyển V2

| Nội dung | Tiểu luận Final V2 | Project01 V2 | Code/bằng chứng |
|---|---|---|---|
| ML/DL, CNN/RNN/LSTM (Q1–18) | Cơ sở toán, loss, gradient, khác biệt kiến trúc; liên hệ assignment | Chọn MLP cho dữ liệu bảng, cohort và hạn chế | `backend/app/ml/`, `../Assignment_04/`, `../Assignment_06/` |
| KG/Cypher (Q19–24,46) | Property graph, ≥5 triples, truy vấn nhiều bước | Schema và 11 assertion thực; ví dụ provenance | `kb_diabetes*.cypher`, `research/graph.py` |
| RAG (Q25–28,47) | Ingest/chunk/embed/retrieve/generate, đối chiếu lexical/vector/graph | 14 nguồn/449 đoạn, admission/checksum, graph candidates và reranker | `research/corpus.py`, `retrieval.py`, `grounding.py` |
| Agent/MAS/RL (Q29–38) | Agent, phối hợp tập trung, MDP/Q-learning, giới hạn tự chủ | Trách nhiệm/input/output/tool, retry/budget, veto | `research/agents.py`, `coordinator.py`, `backend/app/rl/` |
| Ứng dụng DL (Q39–42) | So sánh diabetes/stock/house từ assignment thực | Chỉ diabetes được tích hợp MAS; không nói đã ghép stock/house | `backend/app/ml/`, `../Assignment_02/`, `../Assignment_06/` |
| Tích hợp/demo (Q43–49) | Sơ đồ và liên hệ kiến thức | Web → API → Coordinator → tools → Safety → SQL readback | `docs/architecture.md`, `docs/agent_contracts.md`, trace |
| Đánh giá/hạn chế (Q50–51) | Giải thích metric và phản biện | Baseline cùng budget, failure cases, latency, hạn chế | `experiments/results/final_mas*`, `final_workflows*` |

Không đổi số liệu snapshot thành kết quả V2 mới. Số liệu DL/RL/MAS/LLM trước bổ sung tiếp tục có protocol/timestamp riêng trong `docs/final_handoff.md` và `docs/validation/final_release/release_summary.md`. Completion MAS và baseline cùng 0.863636 ở thí nghiệm offline cũ; 4/6 câu được chấp nhận ở LLM mode trong workflow cũ. Đây không phải clinical accuracy hay bằng chứng MAS vượt baseline.

## Phạm vi sẵn sàng và giới hạn

Kiểm tra mới: 216 backend PASS/43 SKIP, 22 frontend PASS, TypeScript/Vite build PASS; import/readback Neo4j thật PASS. Chrome đã mở màn KB qua gateway có đăng nhập: 11 assertion, lọc triệu chứng còn 3, mở passage, desktop/mobile không có lỗi trang hay tràn ngang ở chiều rộng 390. Ảnh để viết báo cáo: `validation/report_v2/kb-desktop.png` và `kb-mobile.png`. Bản demo native đã được bật tại `http://127.0.0.1:8082`.

Code và nguyên liệu cho hai báo cáo V2 được bổ sung; DOCX/PDF V1 không bị sửa. Kết quả kiểm mới xem `validation/report_v2/`; trạng thái live chỉ được xác nhận bằng log thực. Không có thêm dataset/model/training hoặc metric chất lượng mới. Chưa có nguồn tiếng Việt Vinmec trong corpus allowlist, chưa có pipeline nhập PDF tùy ý. Nếu thầy xác nhận hai điều này là bắt buộc thì cần thêm protocol nguồn, kiểm bản quyền và đánh giá riêng. Docker/cloud và clinical validation vẫn là giới hạn cũ, không đổi thành PASS bằng kiểm tra native.
