# Current traceability — diabetes-grounded expansion before Phase 08

Current user authorization supersedes historical phase limits below. [Current verification report](validation/diabetes_expansion/report.md), [ADR 0007](decisions/0007-diabetes-grounded-llm-runtime.md).

| Requirement | Implementation / evidence |
|---|---|
| Preserve diabetes DL | Frozen trained MLP; actual v2 synthetic prediction persistence; before/after artifact hashes |
| Expand diabetes KG/RAG | 14 versioned NIDDK pages; 449 admitted chunks; 11 source-supported graph assertions; CPU multilingual encoder + cross encoder; no arbitrary model URLs |
| Actual LLM integration | Restricted Groq adapter, strict source-supported claims, secrets outside source; real provider evaluation is credential-dependent and never replaced with a mock metric |
| MAS as the focus | Six typed agents plus Coordinator; correlated tasks, request-local state, bounded retrieval/recomposition feedback, separate verifier, mandatory deterministic veto |
| Stronger grounding | Exact version/URL/quote admission, claim numbers/support, separate semantic review, repeated Coordinator publication checks, rejected-draft erasure |
| Honest failure modes | Extractive / clarification / withheld modes; no graph evidence on graph failure; no fake LLM readiness; missing model/policy/provider and timeout tests |
| Real comparisons | Same-corpus retrieval ablation; same-tool MAS vs direct workflow; offline provider disabled in both; actual CSV/JSON/PNG/manifests, no superiority claim from equal outcomes |
| Existing demo and compatibility | UI uses v2; old v1 endpoints/contracts retained; SQL readback accepts both original schemas; legacy regressions plus new API/browser checks |
| Reproducibility | check_diabetes_expansion.py; dedicated test databases; full source SHA map; current reports, logs and screenshots |

# Traceability Phase 01 (historical)

Yêu cầu người dùng mới là nguồn ưu tiên so với kế hoạch đề xuất Phase 00. Không suy đoán rubric gốc của giảng viên. Không làm Phase 02–08.

| Yêu cầu Phase 01 | Artifact / kiểm chứng |
|---|---|
| Agent protocol, registry, 5 agents | agents/base.py, agents/runtime.py, registry.py; metadata endpoint; registry/agent tests |
| Orchestration có điều kiện | coordinator.py; tests assessment/question/policy-context, demo A/B/C |
| Lifecycle và state transitions | schemas/runtime.py, mas/state.py; transition guard tests |
| Timeout, exception, fallback | wait_for, failed codes, abstention, safety fail closed; tests injection |
| Trace correlation và thứ tự | run_id/message_id/sequence; trace tests và GET trace |
| 4 API MAS | api/mas.py; validation/readback/CORS tests; live HTTP check |
| Cô lập concurrent request | request-local state/registry, app-owned repository lock/deep copy; async HTTP concurrency tests |
| Không fake medical result | 3 tool agents UNAVAILABLE, Education abstention; empty evidence/prediction assertions trong demo |
| Safety tối thiểu | S01/S02/S03 tests; không triển khai full engine Phase 05 |
| Versioned contracts | v1.0 nguyên vẹn; v2.0 bổ sung; ADR 0002 và v1 regression tests |
| Run storage thay thế được | RunRepository Protocol, RAM max 100; copy/eviction/app isolation tests; PostgreSQL Phase 03 chưa làm |
| Demo và docs | scripts/demo_mas.py, docs/mas_workflow.md, docs/validation/phase01/ |

## Kế hoạch Phase 00 (lịch sử, chưa phải roadmap hiện tại)

# Requirements traceability

Bảng dựa trên yêu cầu giao việc của người dùng; chưa đọc/đối chiếu rubric hoặc đề gốc của giảng viên. Không khẳng định các phase dưới đây là lịch giảng viên phê duyệt; đây là kế hoạch đề xuất để theo dõi.

| Yêu cầu | Artifact / kiểm chứng Phase 00 | Phase thực thi nghiệp vụ đề xuất |
|---|---|---|
| MAS trọng tâm, 5 agent + Coordinator | mas/registry.py, coordinator.py, architecture.md; stub tests từng agent | 06 tích hợp |
| Python state-machine, lỗi/timeout/trace | dispatch scaffold + failure tests; chưa có workflow state transitions end-to-end | 06 |
| 8 Pima features và contracts versioned | schemas/contracts.py; validation/roundtrip tests | 00 khóa nền, cập nhật có migration |
| FastAPI, CORS, logging, handler | main.py + api/system.py; health/CORS tests, live HTTP check | 00 |
| React/Vite/TypeScript Home | frontend/src; build log thực tế | 00 |
| PostgreSQL/SQLAlchemy/Alembic | db/session.py, migrations skeleton, compose; chưa xác minh DB live | 01 |
| Deep Learning/PyTorch/sklearn/Jupyter | optional dependency + ml/notebooks/artifacts dirs; chưa cài model | 02 |
| Neo4j/RAG có nguồn | EvidenceItem + knowledge/rag dirs; không evidence giả | 03 |
| Rule-Based safety | SafetyDecision + spec; chưa có rules nghiệp vụ | 04 |
| RL educational policy | RLDecision + spec; chưa có train/inference | 05 |
| UI workflow, persistence, trace | chưa triển khai | 07 |
| Đánh giá, reproducibility, báo cáo | chưa có metric/biểu đồ/kết quả huấn luyện | 08 |
| Dữ liệu/secret/an toàn/tái sử dụng | .gitignore, .env.example, AGENTS.md; fixture SYNTHETIC; không dùng assignment code | mọi phase |
| Test, docs, kết quả thực tế | backend/tests, docs/validation, scripts/verify_phase00.py | 00 và mọi phase |

Không có chức năng phase sau nào được đánh dấu hoàn thành chỉ vì tồn tại folder hoặc class.
