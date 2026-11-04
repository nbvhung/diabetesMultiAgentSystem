# GlucoLab — giao diện tham khảo Nutriwise

**NUTRIWISE_INSPIRED_UI_VERIFIED** · 2026-11-03T06:39:25.906016+00:00. Thực hiện theo yêu cầu tham khảo project `D:\intern\nutriwise-fe`; chỉ đọc project tham khảo. Chọn **trang chủ / HeroSection** làm mẫu màu và typography, kết hợp sidebar và card dashboard để phù hợp không gian nghiên cứu diabetes. [Kết quả máy đọc](results.json).

## Thiết kế đã triển khai

- **Be Vietnam Pro** giống `app/layout.tsx` của Nutriwise; tự host năm weight 400–800, đủ Latin/Vietnamese/Latin Extended. Font lấy từ package `@fontsource/be-vietnam-pro` đã có trong project tham khảo; giữ nguyên [SIL Open Font License](../../../frontend/public/fonts/be-vietnam-pro/OFL.txt). Không gọi Google Fonts hoặc thêm dependency UI.
- Theo `HeroSection.tsx`: nền emerald-50 → trắng → teal-50, tiêu đề sans-serif đậm với chữ gradient emerald-600 → teal-600, CTA gradient và CTA viền xanh. Loại bỏ chữ serif và bảng màu olive trước đó.
- Sidebar trắng với lựa chọn emerald/teal, các card trắng bo 12–17px, hero bo 24px; viền nhẹ, shadow mềm, icon theo nhóm chức năng. Font, nút, biểu mẫu, citations, monitor và nghiên cứu sử dụng cùng hệ thống màu.
- CSS thay toàn bộ stylesheet cũ; có breakpoint 1200/1000/700/360px, focus bàn phím, reduced motion. Không sao chép profile, thống kê dinh dưỡng hoặc mock data của Nutriwise. Các con số, evidence và trạng thái vẫn đọc từ API GlucoLab.

## Kiểm chứng thực tế

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| Frontend unit / Vitest | 22 PASS | [Log](frontend_unit.log) |
| TypeScript + Vite build | PASS | [Log](frontend_build.log) |
| Browser + API thật | 6 PASS, 0 skip/flaky/fail | [Log](browser.log), [JSON](browser-results.json) |
| Font trên trình duyệt | Body và hero là Be Vietnam Pro; font đã load, không lỗi font | [Visual checks](visual-checks.json) |
| Responsive | Tổng quan: 320/360/390/768/1024/1280/1440px; hỏi đáp: 320/390/768/1024/1440px; không tràn ngang | [Visual checks](visual-checks.json) |
| Runtime frontend | Không có page error trong capture và workflow happy path | Browser JSON + visual checks |
| Artifact DL/RL | SHA256 giữ nguyên so với Phase 07 | results.json |

Sáu browser scenario chạy actual FastAPI, PostgreSQL, Neo4j, model và RL: assessment synthetic → sáu agent → citations → đọc lại trace; yêu cầu insulin bị Safety veto; lỗi Neo4j được tiêm có kiểm soát và không citation; biểu đồ thật và lọc nhóm; mobile navigation/topic shortcut; evidence yếu yêu cầu làm rõ với lượt truy hồi có giới hạn. Hai QA API dùng port 18000/18001, provider bị tắt chủ động để không tiêu quota Groq; chế độ extractive/fallback vẫn được ghi đúng. Không dùng kết quả agent hardcode để kiểm chứng tích hợp.

Capture giao diện riêng dùng backend hiện hữu và readiness thật; không gửi thêm câu hỏi đến Groq. Không chạy lại training, full backend suite hoặc tính lại các metric nghiên cứu cho thay đổi UI này. Đây không phải kiểm định lâm sàng hoặc chứng nhận WCAG.

## Ảnh chụp trình duyệt

![Desktop](overview-desktop.png)

[Tổng quan đầy đủ](overview-live.png) · [Hỏi đáp](knowledge.png) · [Mobile tổng quan](mobile-live.png) · [Mobile hỏi đáp](knowledge-mobile.png) · [Assessment thực](assessment.png) · [Monitor](monitor.png) · [Experiments](experiments.png) · [Safety veto](unsafe.png) · [Neo4j unavailable](knowledge-unavailable.png).

Desktop và mobile được xem trực tiếp để rà bố cục; các ảnh scenario ghi lại browser chạy thật. Backend 8000 và frontend 5173 của người dùng được giữ chạy, hai QA API đã dừng sau test. Mở `http://localhost:5173` để xem giao diện mới. Phase 08 chưa triển khai; các giới hạn nghiên cứu trong [bản review](../../project_review_uiux.md) vẫn còn nguyên.

Các lệnh đã chạy từ thư mục dự án:

```powershell
python -X utf8 .tools/nutriwise_ui/verify.py
node .tools/nutriwise_ui/capture.cjs
python -X utf8 .tools/nutriwise_ui/report.py
```

Lệnh chuẩn có thể chạy từ frontend: `npm test`, `npm run build`. Helper cục bộ `.tools/nutriwise_ui/verify.py` gọi đúng Vitest/Vite và Playwright CLI, tự quản lý hai QA API để không thay thế backend đang chạy. Cấu hình kiểm thử chính vẫn ở `frontend/playwright.config.ts` và `frontend/e2e/workflows.spec.ts`.
