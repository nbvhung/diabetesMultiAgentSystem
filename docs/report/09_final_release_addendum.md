# Bản chốt native — số liệu bàn giao

**FINAL_NATIVE_RELEASE_VERIFIED** · 2026-11-04T17:25:08.980232+00:00. Có thể dùng bản này để demo native và viết báo cáo tổng hợp. Không đổi nghiệm thu Docker chưa chạy thành PASS. Cloud hosting NOT_COMPLETED. [Machine results](../validation/final_release/release.json), [kiểm thử](../validation/final_release/final_checks.json), [handoff](../final_handoff.md), [bài tham khảo](../reference_final_review.md).

## Phần mềm thực thi

- Backend **257 PASS**, không skip; [log](../validation/final_release/backend_tests.log).
- Frontend **22 PASS**, production build PASS; [unit](../validation/final_release/frontend_unit.log), [build](../validation/final_release/frontend_build.log).
- Browser/API **6 PASS**, zero skipped/flaky/fail; [JSON](../validation/final_release/browser-results.json), [log](../validation/final_release/browser.log).
- Launcher native chạy thật: model/Q-policy/encoder/reranker load, migration/seed, React build, API riêng 18082 và gateway 8082.
- Ba scenario qua authenticated HTTP gateway: assessment synthetic → genuine LLM/evidence/SQL readback; insulin → BLOCKED; thiếu evidence → clarification. [Output thật](../validation/final_release/native_smoke.json).
- Model/policy frozen không thay, không train lại. Experiments lịch sử không ghi đè; API chỉ trả bundles có checksum đúng.

## Kết quả mới để đưa vào báo cáo

| Control | Runs | Completion | Conditional evidence relevance | Safety invariant | Mean latency ms |
|---|---:|---:|---:|---:|---:|
| single_workflow | 44 | 0.863636 | 0.65 | 1 | 1303.84 |
| multi_agent | 44 | 0.863636 | 0.65 | 1 | 1768.23 |

Nguồn: final_mas.csv/JSON/manifest. Cùng maximum hai retrieval rounds, hai draft rounds, bốn provider attempts; 22 cases × hai repeats/method, paired/shuffled seed 42. Provider disabled cả hai. Kết quả hòa về completion/evidence/safety, không chứng minh MAS thắng về chất lượng. Latency là descriptive trên máy này, có các tác vụ xác minh khác chạy cùng thời gian; không có kết luận speedup nhân quả.

| Language | Questions | Relevant evidence rate | Accepted LLM coverage | Mean latency ms |
|---|---:|---:|---:|---:|
| vi | 3 | 1 | 0.666667 | 4368.76 |
| en | 3 | 1 | 0.666667 | 3143.49 |

Nguồn: final_workflows.csv/rows/JSON/manifest. Sáu câu vi/en đã xem trước qua Coordinator, có retries, actual provider và SQL readback; 6/6 có evidence thuộc relevant source-section, 4/6 được phát hành ở LLM mode sau automated verification. Một fallback vì schema retry hết lượt, một vì Groq rate limit; không tự giả đáp án khi provider lỗi. Có một Vietnamese response phục hồi sau schema rejection. Không mô tả 4/6 là medical accuracy hoặc quy chênh lệch tiếng Việt cho retry bằng kiểm định thống kê. Source relevance là nhãn section thô, không human claim correctness.

## Chạy, đóng gói và giới hạn

`python scripts/start_final_demo.py start` → http://127.0.0.1:8082; user demo, password trong ignored .env.demo. `status` kiểm process; `stop` chỉ dừng owned API/gateway, giữ database. Có thể thêm --tunnel khi start mới và đọc URL thật; không dùng link tunnel cũ như địa chỉ cố định.

`python scripts/package_final_release.py` tạo source.zip + artifacts.zip + manifest ở .tools/exports/final_native_release. Source giữ Markdown/notebooks/code/CSV/JSON và report figure assets nhỏ; artifact archive giữ trusted checkpoints, retrieval weights, corpus, measured figures, không raw Pima/env/DB dumps. Đây là handoff có dependency, không executable độc lập. Không public archive khi quyền tái phân phối Pima-derived weights chưa xác minh.

Gate còn lại: Docker engine/WSL chưa có; chưa kiểm build/start/restart/volumes trên container, cloud hosting chưa làm. Chốt phạm vi native/report-writing, không tuyên bố READY_FOR_DEFENSE theo tiêu chí Docker cũ. Các giới hạn Pima/simulator/same-provider reviewer giữ nguyên. Bộ 48 trang và snapshot Phase 08 là tài liệu lịch sử; dùng bản bổ sung này cho số liệu cuối.
