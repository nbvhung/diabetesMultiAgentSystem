# Quyển báo cáo cuối kỳ — Diabetes Multi-Agent Intelligent Support System

**[Đọc PDF 48 trang](tieuluan_final_06_13_hungnbv.pdf)** · **[Bản Word có thể chỉnh sửa](tieuluan_final_06_13_hungnbv.docx)**

Bìa đã được người dùng xác nhận: Nguyễn Bá Việt Hùng — B23DCCN358, nhóm 13/lớp 06; PGS.TS. Trần Đình Quế. Hình thức tham khảo tiểu luận 03; nội dung theo năm chương trong ảnh đề cương. Có 19 hình trong quyển, bảng dữ liệu/metrics trích từ CSV, source captions, tài liệu tham khảo, code excerpts và phụ lục 32 câu hỏi phản biện. Figures catalog có thêm một ảnh mobile không đưa vào thân quyển.

**Trạng thái nghiệm thu: BLOCKED**, không xác nhận 100% vì Compose runtime chưa chạy trên host thiếu Docker engine/WSL. Native + HTTPS demo đã được kiểm tra. Cloud hosting NOT_COMPLETED. Trạng thái này được ghi ở đầu và kết luận quyển; không biến giới hạn khoa học thành tuyên bố thành công.

## Nguồn để chỉnh sửa

- [Chương 1: Giới thiệu](01_introduction.md).
- [Chương 2: Hệ đa agent](02_multi_agent.md).
- [Chương 3: Kiến trúc tổng quan](03_architecture.md).
- [Chương 4: Các thành phần](04_components.md).
- [Chương 5: Code, demo và đánh giá](05_demo_evaluation.md).
- [Tài liệu tham khảo](06_references.md).
- [Bảng kết quả được sinh từ CSV](07_measured_tables.md).
- [Phụ lục source/demo/phản biện](08_appendix.md).
- [Manifest bản quyển](build_manifest.json), [source inventory](source_inventory.json), [figure captions/sources/hashes](figures/catalog.json).

DOCX/PDF dùng cùng tám file nguồn. PDF được xuất bằng **Chromium**, có mục lục với số trang đo từ PDF thật và links nội bộ; DOCX có Word TOC field riêng. Word native PDF export không hoàn tất, nên không nhận PDF là output Word. Số trang hai renderer có thể khác. Mục lục DOCX đã được cập nhật bằng Word; khi tự sửa tiếp, dùng Ctrl+A/F9. [Kiểm tra render](../validation/phase08/report_layout/checks.json) và contact sheets nằm trong validation/phase08/report_layout.

## Tái tạo tài liệu

Cần Python report extra, Pandoc và Chromium/Playwright. Pandoc là công cụ cài riêng, không nằm trong backend container. Nếu Chromium chưa được cài, chạy `npx playwright install chromium` trong frontend.

```powershell
python -m pip install -e ".[report,ml,knowledge,semantic]"
python scripts/generate_report_assets.py
python scripts/build_final_report.py
# Có Microsoft Word, chỉ cập nhật DOCX TOC:
.\scripts\update_report_toc.ps1
python scripts/build_report_pdf.py
python scripts/inspect_report.py
```

`build_final_report.py` kiểm hashes của measured bundles. `measurement_lock.json` khóa CSV cho các kết luận đã biên soạn; nếu chạy lại evaluator có output khác, phải version/lưu artifact mới và đọc lại nội dung trước khi đổi lock. Không tự giữ kết luận cũ bên cạnh bảng số mới. Build/report tooling không huấn luyện model, gọi Groq hoặc tạo metric mặc định khi thiếu artifact.

Source diagrams được dựng bằng Matplotlib từ spec JSON gắn source; charts copy từ actual experiment PNG, trace render từ actual HTTPS run và screenshot chụp bằng Chromium. Không dùng image generation hoặc bịa hình số liệu. Có captions giải thích khác biệt giữa sơ đồ, measurement và screenshot.

## Handoff dữ liệu demo

Một archive local đã được tạo và đọc lại để kiểm SHA256 toàn bộ 157 file:

`diabetes-mas-final/.tools/exports/diabetes-demo-artifacts.zip` — khoảng 984 MB, bao gồm model/policy, pretrained retrieval weights, corpus snapshot và experiments; không có `.env`, raw Pima hoặc database dumps. SHA256 archive nằm trong file `.manifest.json` cùng thư mục. Archive là local handoff, không tự upload/public; quyền tái phân phối Pima-derived artifacts chưa được xác minh.

Trên bản source mới/rỗng, kiểm archive hash trước rồi giải nén vào root. Không giải nén lên bản demo frozen đang dùng nếu chưa so phiên bản. Có thể tự tạo bundle khác bằng `python scripts/package_demo_artifacts.py --include-retrieval`; script không ghi đè archive cũ. [Hướng dẫn tái lập](../installation.md) phân biệt restore checkpoint và train lại.
