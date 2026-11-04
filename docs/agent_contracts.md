# Current runtime 3.0 — explicit v2 migration

Canonical new contracts: `backend/app/research/schemas.py`; agent declarations: `research/agents.py`. [ADR 0007](decisions/0007-diabetes-grounded-llm-runtime.md) adds `/api/v2`, preserving runtime 2.4 on `/api/v1` and historical base contracts. Persisted snapshots retain their original version; v2 GET validates either version without relabeling. Existing SQL JSON storage needs no DDL change. Prediction serving 1.1 and the trained model/policy are unchanged.

| Agent | Runtime 3.0 input → output | Tools / authority |
|---|---|---|
| prediction | Synthetic PredictionTask → frozen PredictionResult 1.1 | Validated MLP inference, transactional prediction repository; no training |
| knowledge | Question, bounded query, attempt → evidence, topic coverage, adequacy, method | Neo4j release read, local lexical/dense retrieval and cross encoder; no arbitrary Cypher/URL |
| rl | Prediction/evidence → whitelisted educational RLDecision | Frozen Q-policy or declared fallback; simulator context, no clinical actions |
| education | Question/language/evidence/action/reason-only feedback → atomic claims or exact-source fallback | Bounded Groq composition; cannot admit its own claims |
| verifier | Original question/candidate/evidence → verdict, candidate SHA256, checked claims, reason codes | Exact corpus/quote/number/rendering checks plus separate Groq semantic review; may reject |
| safety | Input or output with provenance/action metadata → SafetyDecision 3.0 / diabetes-safety-2.0 | Deterministic rule gates; cannot be waived by caller or LLM |

`Message` correlates run/message IDs, recipient and typed task. `Result` validates agent/output/status matching. `Event` records sequence, attempt, duration, redacted input/output metadata and decisions. No raw prompt, assessment values, provider body or rejected draft in trace summaries. At most two retrieval attempts, two drafts and four remote attempts; unavailable/failed agents never return fabricated business output.

`Evidence` binds SHA256 ID, exact registered URL, publisher, immutable source version, retrieved timestamp, parent section context and exact excerpt. Source admission compares these fields against the prepared release. `Claim` requires exact quote/ID supports. Separate `VerifierOutput` must match the rendered candidate digest; Coordinator repeats deterministic checks before output Safety. LLM mode requires genuine provider metadata plus independent semantic-review mode. Extractive/clarification/withheld are separate response modes, never fake generated answers. Response invariants require all six terminal agent results, both Safety gates and correlated ordered trace; degraded/block/failure semantics remain explicit.

Current HTTP additions: `/api/v2/mas/runs`, `/{id}`, `/{id}/trace`, `/mas/agents`, `/system/readiness`, `/knowledge/sources`, `/knowledge/graph`, `/knowledge/search`. Experiment reports remain served by the checksum-verified `/api/v1/experiments` projection, with additive diabetes bundle names. See [grounding](llm_grounding.md) and [current guide](diabetes_expansion_demo.md). The historical sections below describe their original phases.

# Phase 07 integration (historical) — existing v1 contracts retained

Frontend sends RunInput runtime 2.4 to the existing Coordinator endpoint. Base contracts v1.0, serving PredictionResult 1.1, EducationOutput 1.1 and SafetyDecision 1.1/policy safety-1.1 remain unchanged. No expanded agent tool permissions, new agent payloads or DDL. UI status/score/action/evidence/trace are read from WorkflowResponse, not synthesized.

Additive read-only endpoints: `GET /api/v1/system/readiness` returns dependency probe status/version/time; `GET /api/v1/experiments` returns verified offline reports/manifests or unavailable; `GET /api/v1/experiments/{name}/figure` serves the PNG listed in a valid manifest. These are system/evaluation API projections, not agent contract mutations. Agent input/output summaries in the monitor are an explicit allowlist of existing response metadata. Historical contracts and migrations follow.

# Agent contracts v1.0 (historical base, still importable)

Nguồn chuẩn: `backend/app/schemas/contracts.py`. Mọi schema kế thừa Contract có `schema_version: Literal["1.0"]`, extra=forbid, cấm NaN/Infinity. UUID cho run/message; timestamp bắt buộc timezone. Thay đổi phá vỡ tương thích phải có version mới, ADR/migration và contract tests; không âm thầm đổi field ở phase sau.

| Schema | Contract |
|---|---|
| AssessmentInput | pregnancies:int >=0; glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree:float >=0; age:int >=1; 8 field bắt buộc |
| AgentMessage | message_id:UUID auto, run_id:UUID, sender/recipient:coordinator hoặc enum 5 agent, message_type:task/result/error, payload:dict JSON, timestamp:aware UTC auto |
| AgentResult | agent_name:enum, status:success/stub/unavailable/error/timeout, output:typed output union hoặc None, errors:list[str], evidence_ids:list[str] |
| PredictionResult | model_id, model_version:str; predicted_class:0/1; score:[0,1]; limitations:list[str] không rỗng |
| EvidenceItem | evidence_id, source_title, publisher, section, excerpt:str; source_url:HTTP(S); retrieved_at:aware datetime |
| RLDecision | state:dict JSON, action:str, policy_version:str, decision_source:policy/fallback |
| SafetyDecision | allowed:bool, severity:info/warning/critical, rule_ids:list[str], reason:str |
| WorkflowState | run_id:UUID auto, request:AssessmentInput, agent_results:dict[AgentName,AgentResult], trace:list[TraceEvent], errors:list[str], final_response:str hoặc None |
| WorkflowResponse | run_id:UUID, status:completed/stub/failed, response:str, evidence:list[EvidenceItem], agent_trace:list[TraceEvent] |
| KnowledgeOutput | evidence:list[EvidenceItem] |
| EducationOutput | text:str, evidence_ids:list[str] |
| TraceEvent | agent_name, status như AgentResult, timestamp:aware UTC auto |

Zero được cho phép ở field số liên tục để giữ raw Pima input; Phase 00 không tự coi zero là thiếu hay chuẩn hóa. Đơn vị dự kiến: glucose mg/dL, blood_pressure mmHg (tâm trương), skin_thickness mm, insulin µU/mL, BMI kg/m², tuổi năm; diabetes_pedigree là chỉ số không đơn vị. Validation hiện chỉ là cấu trúc, không xác nhận tính hợp lý lâm sàng. Không diễn giải score là xác suất hiệu chỉnh khi chưa có đánh giá/calibration.

Output union được kiểm soát bằng cross-field validator: success bắt buộc output đúng schema của agent và errors rỗng; mọi status khác success bắt buộc output=None. Có invariant tests cho từng agent. Mọi thay đổi payload ở phase sau phải có version/migration và cập nhật tests. Stub implementation luôn output=None; không tạo PredictionResult giả. JSON payload là envelope vận chuyển, không tự đồng nghĩa đã qua input validation nghiệp vụ.

| Agent | Trách nhiệm / input → output | Chính sách mục tiêu | Planned tool (Phase 00: tất cả disabled) |
|---|---|---|---|
| prediction | Risk inference: AssessmentInput → PredictionResult | Chỉ dùng model đã load, có version; thiếu model trả unavailable | torch_inference |
| knowledge | Truy hồi: request + query → KnowledgeOutput | Chỉ evidence có nguồn, không tự bịa trích dẫn | neo4j_read, rag_retrieve |
| education | Giải thích: prediction + evidence + RL action → EducationOutput | Có dẫn chứng, abstain nếu thiếu evidence | evidence_read |
| safety | Input/content → SafetyDecision | Fail closed nếu rules chưa sẵn sàng, chặn ngôn ngữ chẩn đoán chắc chắn | rule_evaluate |
| rl | Educational state → RLDecision | Chọn trong allowed actions bằng policy versioned; fallback phải khai báo rõ | policy_inference |

`AgentSpec` lưu trách nhiệm, input/output, decision_policy, planned_tools và enabled_tools. Mỗi agent có test parametrized riêng với tên agent trong pytest ID. Đây là spec và stub riêng theo cấu hình, không phải 5 tích hợp hoạt động. Context query/educational state và payload ghép cho các task tương lai chỉ mới là mô tả, chưa có task-specific input schemas; phải khóa chi tiết trước khi tích hợp.

Semantics: available = có chức năng hiện dùng được trong phạm vi công bố; stub = chỉ khung, không output nghiệp vụ; unavailable = chưa sẵn sàng hoặc chưa kiểm chứng dependency; success = task thực hiện thành công; error = lỗi xử lý; timeout = vượt hạn. Capabilities không dùng success/error/timeout. `health=ok` chỉ là liveness. Workflow completed chỉ dành cho luồng thật đã qua safety; Phase 00 không tạo completed. `errors` dùng mã lỗi, không chứa PHI/secret. Evidence IDs phải truy nguyên được trong pha tích hợp; bootstrap chưa sinh evidence.


## Runtime Phase 01 v2.0 (ADR 0002)

Phần v1.0 phía trên được giữ như lịch sử contract Phase 00. Runtime hiện tại nằm ở `schemas/runtime.py`; không thay v1.0. [ADR 0002](decisions/0002-runtime-contracts.md) giải thích versioning và thay đổi đường import Coordinator.

| Contract v2.0 | Field / invariant |
|---|---|
| RunInput | assessment:AssessmentInput v1 hoặc None, question:str 1–4000 sau trim hoặc None; phải có ít nhất một; extra forbidden |
| PredictionTask | assessment:AssessmentInput v1 bắt buộc |
| KnowledgeTask | question:str 1–4000 |
| RLTask | prediction:PredictionResult hoặc None, evidence:list[EvidenceItem] |
| EducationTask | question, prediction, evidence, decision:RLDecision hoặc None, warnings:list[str] |
| SafetyTask | question hoặc None, candidate:str bắt buộc |
| AgentMessage | message_id/run_id UUID, sender=coordinator, recipient enum, message_type=task, payload union có validator khớp recipient, timestamp aware |
| AgentResult | agent_id enum, lifecycle status, implementation=stub/minimal, output đúng output type nếu COMPLETED, errors:list[str]; stub không thể COMPLETED; non-completed output=None |
| WorkflowState | run_id, request:RunInput, workflow status, agent_results, trace, warnings, errors, final_response |
| TraceEvent | sequence>=1, run_id UUID, agent_id/message_id optional, status enum agent/workflow, reason mã, timestamp aware |
| WorkflowResponse | run_id, status, agent_results, response (final response), evidence, agent_trace, warnings, limitations |

Mọi runtime schema có `schema_version=2.0`; output nghiệp vụ bên trong vẫn version 1.0. AgentDefinition immutable công bố agent_id, description, input_schema, output_schema, permitted_tools, implementation, available, timeout_seconds, fallback_policy, status_semantics. BaseAgent Protocol yêu cầu definition và execute(AgentMessage) → AgentResult async. AgentRegistry register/get/definitions có kiểm tra duplicate và timeout hữu hạn dương. Không tool nào được cấp ở Phase 01.

| Agent | Runtime input → output | Phase 01 policy / fallback | Timeout |
|---|---|---|---|
| prediction | PredictionTask → PredictionResult | Stub UNAVAILABLE/TOOL_NOT_INTEGRATED; không tính score | 1s |
| knowledge | KnowledgeTask → KnowledgeOutput | Stub UNAVAILABLE; evidence=[] trong workflow | 1s |
| rl | RLTask → RLDecision | Stub UNAVAILABLE; Coordinator chỉ dispatch khi policy available và có valid context; không fake action | 1s |
| education | EducationTask → EducationOutput | Minimal transparent abstention; lỗi/timeout → Coordinator dùng abstention cố định và vẫn gọi Safety | 1s |
| safety | SafetyTask → SafetyDecision | Minimal rules; veto → BLOCKED; lỗi/timeout/mất agent → FAILED và giữ lại nội dung | 1s |

Status và state transitions, tracing/correlation, redaction, storage semantics được mô tả đầy đủ ở [mas_workflow.md](mas_workflow.md). `COMPLETED` là task kết thúc có output hợp lệ, không đảm bảo model/clinical correctness và Safety COMPLETED vẫn có thể allowed=false. Các stub được công bố implementation=stub dù runtime status=UNAVAILABLE; không nhầm với lifecycle COMPLETED. Workflow DEGRADED vẫn có response giới hạn, evidence rỗng khi retrieval unavailable. Timeout là FAILED với errors=[AGENT_TIMEOUT].

Khóa contract: cập nhật payload/status semantics cần ADR/version thích hợp và test; invariant tests v1 vẫn chạy. Test injection có thể dùng evidence/policy SYNTHETIC để xác minh routing, không bật chúng trong app hoặc demo.


## Phase 03 update — runtime 2.1, serving output 1.1

Current schema is runtime 2.1, superseding historical 2.0 above; contracts.py v1.0 remains unchanged. See ADR 0003. RunInput adds is_synthetic: Literal[True] or None; integrated API rejects assessments without explicit true. Assessment still has exactly eight Pima fields; numeric strings/bools are rejected using strict validation on raw JSON. No assessment means prediction SKIPPED, no insert. Nonfinite/negative/missing features return 422.

Prediction output schema 1.1 adds preprocessing_version (SHA256 of fitted joblib), inference_latency_ms (transform/model only, excludes lazy load/DB), warnings:list[str], persisted_record_id:UUID. score is an uncalibrated sigmoid output, predicted_class uses frozen 0.5 threshold; neither is a diagnosis. Required model_id/model_version identify real Phase 02 artifact. Output can never be random fallback. Integrated AgentResult requires COMPLETED and typed output; metadata permitted_tools is pytorch_inference/postgres_prediction_write. Tools act only on synthetic-confirmed integrated API requests; standalone service inference does not authorize persistence.

TraceEvent 2.1 adds optional model_version and inference_latency_ms populated on prediction completion and stored in event JSON. Response/GET trace schema_version=2.1. Explicit 2.0 clients must migrate; no silent contract mutation under old version.

Input range policy: accept finite nonnegative values allowed by AssessmentInput, warn OUTSIDE_TRAINING_RANGE:<feature> for raw value outside min/max in train-only serving.json; no clipping or silent adjustment. Zero in fixed five fields gets ZERO_TREATED_AS_MISSING warning and exact training median imputation; pregnancies zero preserved. Adults outside cohort age range also warned. This is distribution support checking, not clinical reference limits. Scores at extreme inputs are not validated for use. Preprocessing and weights never refit on requests.

Model/DB failures: artifact absence, checksum/version/feature/device mismatch => model unavailable, no output or prediction row. DB write failure => entire transaction rollback and HTTP 503, no persisted success returned. GET storage unavailable => 503, unknown/no snapshot => 404. Synthetic confirmation required only in integrated assessment path; explicit legacy factory remains for prior phase unit fixtures.


## Phase 04 — Knowledge and grounded Education

Runtime 2.1 and EvidenceItem v1 remain unchanged. Knowledge implementation=integrated, tools neo4j_read/hybrid_retrieval, timeout 15s. Output KnowledgeOutput has exact retrieved evidence IDs/excerpts/URLs; metadata version/date/usage is preserved on Source/DocumentChunk and linked by evidence_id. Empty completed retrieval emits NO_EVIDENCE trace reason/warning, not a new lifecycle enum or fabricated evidence; infrastructure failure emits UNAVAILABLE/NEO4J_UNAVAILABLE. Education implementation=integrated, deterministic excerpt template + IDs/URLs, abstains without admissible evidence. No LLM. Safety still gates final content. See rag_pipeline.md for limitations and evaluation semantics. No DL/RL contract changes.


## Phase 05 current contract — runtime 2.2 and SafetyDecision 1.1

Supersedes historical runtime 2.1 sections above; contracts.py v1.0 unchanged. New safety.py subclass adds decision, stage, checked_content (counts/presence only), timestamp, policy_version=safety-1.0; inherited allowed must match decision, rule_ids nonempty. SafetyTask gains input/output stage, assessment context, admitted/cited IDs, provenance/grounding/abstention flags, prediction/knowledge status and proposed action. Context is assembled by Coordinator, never accepted as permission flags from RunInput user JSON.

WorkflowState/Response keep ordered safety_decisions [input,output]. Terminal response validator requires both and rejects released status if any veto. TraceEvent includes rule_ids, safety_decision, safety_stage. Default SafetyAgent integrated; repeated execution permitted only for the output gate; direct business dispatch needs current preflight and no latched denial. Policy actions ALLOW/ALLOW_WITH_WARNING permit continuation; BLOCK/ESCALATE/REQUEST_CLARIFICATION stop it. Workflow status BLOCKED with explicit decision details, FAILED for system safety failure.

Stored 2.1 snapshots need separate safety review; GET returns 409 instead of bypassing current policy. Details in ADR 0004, rule_catalog.md and safety_policy.md. No synthetic clinical evidence or historic rule results fabricated.


## Phase 06 current runtime 2.3 — educational RL

Runtime 2.3 supersedes prior 2.2; v1 AssessmentInput/RLDecision, serving PredictionResult 1.1 and SafetyDecision 1.1 unchanged. RLTask adds simulated_knowledge_level and simulated_engagement_level (low/medium/high, medium default), safety_status normal/restricted from preflight. These fields are internal task context, not user-set assessment facts. RLDecision.state explicitly labels SIMULATED_DEFAULTS_NOT_MEASURED, encoder state, band/evidence status and decision_reason. Action comes only from the six education actions in rl/mdp.py.

TraceEvent adds policy_version/action/decision_source, set on completed RL tasks. Current run/trace/snapshot version 2.3; prior stored snapshots need explicit migration/review through existing 409 path, not invented historical RL outputs. No DDL changes. Real integrated RL agent is called with empty evidence/model to choose safe next interaction; historical fixture stub behavior remains for tests. Policy artifact missing/corrupt/out-of-domain/unvisited state returns explicit baseline fallback with fallback-rule-1.0 and source=fallback. No request-time learning. Safety veto remains latched; output trace recommendation is redacted on veto. See ADR 0005 and rl_mdp.md.


## Phase 06 remediation — current runtime 2.4

ADR 0006 supersedes 2.3: completed RL outputs are whitelist-checked before trace/forwarding; invalid output is sanitized FAILED/RL_ACTION_NOT_ALLOWED, followed by independent Safety W04 veto. WorkflowResponse rejects non-whitelisted completed actions (only a blocked/failed redaction marker is exempt). Frozen RLDecision v1 unchanged.

EducationOutput subclass 1.1 adds proposed_action/effective_action/override_reason; metadata must use canonical actions and mismatches require a reason. TraceEvent adds proposed_action/effective_action/action_override_reason. Current response distinguishes recommendation from the rendered clarification fallback. Veto redacts both. SafetyDecision schema 1.1 retains fields, policy_version now safety-1.1 for new whitelist rule. Model serving contract unchanged. JSON snapshots use runtime 2.4; previous versions are not silently rewritten. No SQL DDL needed. Policy artifact now education-q-1.1 with serving-policy evaluation definition pinned in format 1.1 manifest.
