# Phase 08 — nghiệm thu cuối

**BLOCKED — Docker runtime chưa chạy được trên host thiếu Docker engine/WSL.** Native demo, HTTPS tạm và bộ báo cáo đã hoàn thành/kiểm chứng. Cloud deployment **NOT_COMPLETED**. Không dùng PASS Phase 07 hoặc parse Compose để ký nghiệm thu 100% Phase 08.

Verified UTC `2026-11-03T10:26:16.001193+00:00`. Code `source-sha256:c7fcf2d3393932af54b5c51b97598c8c8b4126b7229386f5801f5a491e1bd5f0`. [Machine results](results.json), [canonical checker output](final_checks.json), [audit trước báo cáo](../../phase08_scope_audit.md).

## Hoàn thành

- Compose toàn stack: FastAPI, React/nginx, PostgreSQL, Neo4j; initialize migration/seed/load, health dependency, named volumes, read-only artifact mounts, env secrets và development override. Dockerfiles/mounts/config đã có; chạy container thực chưa xác minh.
- Hướng dẫn 12 bước từ source mới; phân biệt checkpoint/restore/train lại. Artifact handoff local 157 files, 984271815 bytes, kèm checksums, gồm pretrained retrieval weights; không có env/raw Pima/DB dumps. Không tự public archive vì quyền tái phân phối Pima-derived artifacts chưa xác minh.
- Báo cáo **48 trang PDF**, Word editable với TOC đã cập nhật, 5 chương đúng ảnh bảng, 19 hình trong quyển, metrics tables từ CSV, nguồn/caption, code excerpts và 32 Q&A. [Quyển và source](../../report/README.md); [layout checks](report_layout/checks.json). PDF xuất bằng Chromium sau khi Word native PDF export không hoàn tất; không nhận hai renderer giống pagination.
- [Demo hai phút](../../defense/demo_2_minutes.md), [tám phút](../../defense/demo_script.md), [slide outline](../../defense/slide_outline.md), [32 Q&A](../../defense/qa.md). Không tuyên bố có PowerPoint deck đã render.

## Thực thi kiểm chứng

| Hạng mục | Kết quả thực | Log / artifact |
|---|---|---|
| Backend full suite | **249 PASS**, không skip; 8 warnings được giữ | [Log](backend_tests.log) |
| Frontend unit | **22 PASS** | [Log](frontend_unit.log) |
| TypeScript + Vite build | Exit 0 | [Log](frontend_build.log) |
| Browser + real APIs | **6 PASS**, 0 skip/flaky/fail | [Log](browser.log), [JSON](browser-results.json) |
| Migration | Head 0002_phase03, exit 0 | [Log](migration.log) |
| Graph/model/policy initialization | 449 chunks, 14 sources, 11 assertions; MLP/Q-policy/encoder/reranker loaded | [Log](initialize.log) |
| Authenticated HTTPS demo | 3 actual scenarios + identical persisted GET readback | [Runs](public_demo.json) |
| Public browser | 0 page errors; mobile no overflow | [Browser](public_browser.json), [final heartbeat](public_heartbeat.json) |
| Artifact integrity | 6 measured bundles verified; frozen DL/RL unchanged | results.json |
| Report render | 48 PDF pages, 19 embedded DOCX figures, no out-of-page text or unresolved refs | report_layout/checks.json |
| Compose config | CLI parse exit 0 | [Log](compose_config.log) |
| Compose startup | **FAIL/BLOCKED**, exit 1: missing docker_engine pipe | [Log](compose_startup.log) |

Test infrastructure uses two named disposable PostgreSQL DBs and a separate Neo4j instance in an ASCII temporary directory; the application's DB/graph remain in place. Test fixture transports are explicitly synthetic for unit tests; browser and end-to-end paths use actual services. Offline regression clears Groq key in the child process; fake-provider unit tests keep LLM enabled to exercise mocked HTTP transport. Previous setup attempts exposed this environment distinction and an unmigrated workflow test DB; runner fixed, expected labels unchanged. The final canonical checker repeats migration/initialize/backend/frontend/browser/integrity and exits 1 **only for the remaining Docker gate**, not because tests failed.

## HTTPS URL và trạng thái vận hành

**https://champion-sonic-dept-charged.trycloudflare.com** — username `demo`, password in ignored `.env.demo`. Temporary tunnel points to built-frontend gateway port 8082, not Vite; backend 8000 and databases remain local. It is not cloud hosting. Gateway requires authentication, rate/payload limits and route allowlist; the backend is not publicly exposed directly. Secret values were not copied into report/source/infra; no key is embedded in React.

The latest authenticated heartbeat returned frontend HTTP 200, anonymous HTTP 401 and identical readback of the three initial runs. First run: six COMPLETED agents, actual MLP score, RL action SHOW_EVIDENCE from policy education-q-1.1, genuine Groq generation, source admission and SQL trace. Insulin scenario BLOCKED with no citations; missing-evidence scenario clarification with no citations. Graph outage is separately covered by isolated fault API in browser regression, not fabricated as an actual outage of the main graph.

The user backend/Vite/Neo4j and the owned gateway/tunnel remain running; QA API/Vite/graph children were stopped. URL expires when tunnel/machine stops. Check `python scripts/demo_host.py status` before defense; `stop` closes only owned gateway/tunnel.

## Kết quả nghiên cứu và giới hạn

MLP accuracy/F1 0.758621/0.611111, LR 0.775862/0.617647; 19/41 test positive labels missed by MLP. Q reward/completion 4.276/0.97 vs rules 4.311/0.983333. Confirmatory hybrid MRR@3 0.625, returned precision 0.570833; semantic recall higher. Offline MAS completion 0.863636 vs direct 0.727273 has different retry budgets, lower conditional relevance and greater latency: no general superiority claim. Saved metrics were not retrained/regenerated in Phase 08 just to improve appearance.

New live Groq benchmark: six questions, three genuine LLM outputs, all three accepted by automated separate verifier; two clarification and one schema-rejection extractive fallback. Coverage **3/6**, conditional acceptance **3/3**; sample outputs accepted are English phrasings. No expert medical accuracy or universal Vietnamese quality claim. Source rows/CSV/JSON/PNG/manifest are preserved in `experiments/results/diabetes_llm*`; rejected output is not published. A medical expert/human-grounding benchmark, matched-budget MAS ablation, broader DL validation and RL realism remain research work.

## Lệnh đã chạy và gate còn lại

```powershell
python -X utf8 .tools/phase08/test_services.py --final
python scripts/check_phase08.py --test-env .env.phase08-test --compose-cli .tools/phase08/docker-compose.exe
python scripts/evaluate_diabetes_llm.py --live --limit 6
python scripts/demo_host.py start --tunnel
python scripts/generate_report_assets.py
python scripts/build_final_report.py
.\scripts\update_report_toc.ps1
python scripts/build_report_pdf.py
python scripts/inspect_report.py
python scripts/package_demo_artifacts.py --include-retrieval
```

The local `.tools` helper prepares dedicated test infrastructure; portable checker is in scripts. Some commands are not idempotent by design: artifact packaging/env setup refuse overwrite, and `start` refuses duplicate processes. Do not rerun these on the running demo without reading status/guides.

To close acceptance: install/use Docker engine with Linux containers, run `docker compose --env-file .env.compose up --build --wait`, verify initialization/health, run actual workflows, restart services and verify volume/readback, save image digests and logs. This cannot be replaced by native tests or YAML parse. Public cloud hosting remains NOT_COMPLETED unless a real independent deployment is configured and checked; cloud is optional for this delivery, Docker runtime is the explicit remaining acceptance blocker. No Git init, commit or push was performed.
