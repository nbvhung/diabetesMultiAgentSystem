# PHỤ LỤC: TRUY VẾT SOURCE, KIỂM THỬ VÀ DEMO

## A. Code excerpts từ implementation

Các trích đoạn dưới đây được lấy tự động từ source hiện tại. Chúng giải thích cơ chế, không thay cho toàn bộ source hoặc output kiểm thử.

### backend/app/research/coordinator.py — từ dòng 39

```python
        async def dispatch(name,payload,attempt=1):
            # Safety can never be skipped or authorized by the caller's input JSON.
            if name!=AgentId.safety and (not decisions or not decisions[0].allowed or len(decisions)>1):raise ValueError('SAFETY_PREFLIGHT_REQUIRED')
            agent=self.registry.get(name)
            if agent is None:
                result=Result(agent_id=name,status=AgentStatus.UNAVAILABLE,errors=['AGENT_UNREGISTERED'])
                results[name]=result;event(name,result.status,'AGENT_UNREGISTERED',attempt=attempt);return result
            message=Message(run_id=run_id,recipient=name,payload=payload)
            event(name,AgentStatus.RUNNING,'TASK_DISPATCHED',message_id=message.message_id,attempt=attempt,input_summary=summary(payload))
            started=time.perf_counter()
            try:
                remaining=max(.001,deadline-time.monotonic())
                raw=await asyncio.wait_for(agent.execute(message),timeout=min(agent.definition.timeout_seconds,remaining))
                result=Result.model_validate(raw.model_dump())
                if result.agent_id!=name or result.status not in (AgentStatus.COMPLETED,AgentStatus.UNAVAILABLE,AgentStatus.FAILED):raise ValueError('Agent identity/status mismatch')
                if name==AgentId.rl and result.output and result.output.action not in ACTIONS:result=Result(agent_id=name,status=AgentStatus.FAILED,errors=['RL_ACTION_NOT_ALLOWED'])
            except TimeoutError:result=Result(agent_id=name,status=AgentStatus.FAILED,errors=['AGENT_TIMEOUT'])
            except Exception:result=Result(agent_id=name,status=AgentStatus.FAILED,errors=['AGENT_EXCEPTION_OR_INVALID_RESULT'])
            results[name]=result
            details={}
            if isinstance(result.output,SafetyDecision):details={'safety_stage':result.output.stage,'safety_decision':result.output.decision,'rule_ids':result.output.rule_ids}
            if isinstance(result.output,RLDecision):details={'action':result.output.action,'policy_version':result.output.policy_version,'decision_source':result.output.decision_source}
            event(name,result.status,result.errors[0] if result.errors else 'TASK_COMPLETED',message_id=message.message_id,attempt=attempt,duration_ms=(time.perf_counter()-started)*1000,output_summary=output_summary(result.output),**details)
            if result.status!=AgentStatus.COMPLETED:warnings.extend(name.value+':'+e for e in result.errors)
```
Nguồn: `backend/app/research/coordinator.py`, SHA256 `927738002e23fcb5f4a44cb7e6787346766747ca268cd5298e5455266e9458f1`.

### backend/app/research/api.py — từ dòng 51

```python
@router.post('/mas/runs',response_model=WorkflowResponse,status_code=201)
async def create_run(payload:RunInput,request:Request):
    svc=services(request);state=request.app.state
    import asyncio
    # One-time CPU model loading happens before opening the SQL transaction and
    # starting agent task budgets. Otherwise cold import alone could exhaust a task.
    from .safety import evaluate
    from .schemas import SafetyTask
    from .retrieval import query_topics
    initial=evaluate(SafetyTask(stage='input',question=payload.question,assessment=payload.assessment.model_dump() if payload.assessment else None))
    if initial.allowed and payload.question and query_topics(payload.question):await asyncio.to_thread(svc.warmup)
    if payload.assessment is not None:
        try:AssessmentInput.model_validate((await request.json())['assessment'],strict=True)
        except ValidationError:raise HTTPException(422,'INVALID_ASSESSMENT_TYPES') from None
    try:
        with state.db_engine.begin() as connection:
            repository=ResearchRepository(connection)
            registry=build_registry(state.model_service,repository,state.policy_service,svc.retriever,svc.llm)
            result=await Coordinator(registry,svc.corpus).run(payload)
            if result.agent_results[AgentId.prediction].status==AgentStatus.FAILED:raise HTTPException(503,'PREDICTION_TRANSACTION_FAILED')
            repository.save(result)
        return result
    except HTTPException:raise
    except Exception:raise HTTPException(503,'RESEARCH_WORKFLOW_OR_PERSISTENCE_UNAVAILABLE') from None


@router.get('/mas/runs/{run_id}')
def read_run(run_id:UUID,request:Request):
```
Nguồn: `backend/app/research/api.py`, SHA256 `ebc5599641e96397083810eb0172063ba668989f7768e1199127c62dbdd2316a`.

### backend/app/ml/pipeline.py — từ dòng 68

```python
class MLP(nn.Module):
    def __init__(self):
        super().__init__(); self.layers=nn.Sequential(nn.Linear(8,32),nn.ReLU(),nn.Dropout(0.15),nn.Linear(32,16),nn.ReLU(),nn.Linear(16,1))
    def forward(self,x): return self.layers(x).squeeze(-1)

```
Nguồn: `backend/app/ml/pipeline.py`, SHA256 `cf411ff60d50309d27c9acba75e27948efad10d54006a876c45710398abe93c6`.

### backend/app/rl/learning.py — từ dòng 1

```python
import numpy as np
from backend.app.rl.mdp import EducationEnv,N_STATES,encode

def td_update(q,s,a,r,next_s,terminated,truncated,alpha,gamma):
    target=r if terminated or truncated else r+gamma*float(q[next_s].max())
    q[s,a]+=alpha*(target-q[s,a])
    return float(target)

def train(seed,episodes=8000,alpha=.15,gamma=.95):
    rng=np.random.default_rng(seed)
    q=np.zeros((N_STATES,6),dtype=np.float64);visits=np.zeros(N_STATES,dtype=np.int64)
    env=EducationEnv(); history=[]
    for episode in range(episodes):
        state,_=env.reset(seed=seed*1_000_000+episode)
        epsilon=max(.05,1.0*(.9994**episode));total=0.;length=0;unsafe=0
        while True:
            row=encode(state);visits[row]+=1
            # Training explores all six educational actions, including unsupported contexts.
            action=int(rng.integers(6)) if rng.random()<epsilon else int(np.argmax(q[row]))
            new,r,term,trunc,info=env.step(action)
            td_update(q,row,action,r,encode(new),term,trunc,alpha,gamma)
            total+=r;length+=1;unsafe+=info['unsafe_attempt'];state=new
            if term or trunc:break
        history.append({'seed':seed,'episode':episode,'reward':total,'length':length,'completed':int(info['completed']),'unsafe_attempts':unsafe,'epsilon':epsilon})
    return q,visits,history
```
Nguồn: `backend/app/rl/learning.py`, SHA256 `fed82e9a3af5d5b9ce301be6b477ad480dc484fdebcdf49fad8fa6b668825915`.

### backend/app/research/grounding.py — từ dòng 65

```python
def publication_errors(candidate,evidence,corpus):
    """Deterministic admission repeated by Coordinator, independent of agent approval."""
    if candidate.generation_mode=='clarification':
        return [] if candidate.text in CLARIFICATION.values() and not candidate.claims and not candidate.evidence_ids else ['UNCONTROLLED_ABSTENTION']
    if any(not corpus.admits(e) for e in evidence):return ['EVIDENCE_PROVENANCE_MISMATCH']
    if candidate.generation_mode=='extractive':
        return [] if evidence and candidate.text==render_extractive(evidence) and set(candidate.evidence_ids)=={e.evidence_id for e in evidence} else ['EXTRACTIVE_CANDIDATE_MISMATCH']
    if candidate.generation_mode=='llm':return validate_claim_support(candidate,evidence,corpus)
    return ['UNRELEASABLE_GENERATION_MODE']


async def verify_candidate(candidate,evidence,corpus,llm,question=None):
    digest=candidate_digest(candidate)
    def report(ok,mode,codes,checked=0,**usage):return VerifierOutput(verified=ok,mode=mode,candidate_sha256=digest,checked_claims=checked,reason_codes=codes,**usage)
    if candidate.generation_mode=='clarification':
        valid=candidate.text in CLARIFICATION.values() and not candidate.evidence_ids and not candidate.claims
        return report(valid,'abstention' if valid else 'rejected',['CONTROLLED_ABSTENTION' if valid else 'UNCONTROLLED_ABSTENTION'])
    if any(not corpus.admits(e) for e in evidence):return report(False,'rejected',['EVIDENCE_PROVENANCE_MISMATCH'])
    if candidate.generation_mode=='extractive':
        valid=bool(evidence) and candidate.text==render_extractive(evidence) and set(candidate.evidence_ids)=={e.evidence_id for e in evidence}
        return report(valid,'exact_quote' if valid else 'rejected',['EXACT_SOURCE_QUOTES' if valid else 'EXTRACTIVE_CANDIDATE_MISMATCH'])
    errors=validate_claim_support(candidate,evidence,corpus)
    if errors:return report(False,'rejected',errors,len(candidate.claims))
    known={e.evidence_id:e for e in evidence}
    data={'question':redact_question(question or ''),'claims':[{'claim_id':c.claim_id,'text':c.text,'source_context':[{'evidence_id':s.evidence_id,'quote':s.quote,'full_passage':known[s.evidence_id].excerpt,'source_title':known[s.evidence_id].source_title,'section_context':known[s.evidence_id].section_context or known[s.evidence_id].section} for s in c.supports]} for c in candidate.claims]}
    try:completion=await llm.complete(purpose='diabetes_evidence_review',system=VERIFY_PROMPT,data=data,schema=Review)
    except LLMUnavailable as error:return report(False,'rejected',['VERIFIER_'+error.code],len(candidate.claims))
    verdicts=completion.parsed.verdicts;ids=[v.claim_id for v in verdicts]
```
Nguồn: `backend/app/research/grounding.py`, SHA256 `e4e090dd9786f5b8f182f8826df93f711b631ef01fc7466a7a8c4f23770891ec`.

## B. Kết quả nghiệm thu cuối

Backend 249 PASS; frontend 22 unit PASS; TypeScript/Vite build PASS; browser/API 6 PASS. Migration head, seed, model/policy/encoder/reranker loads và ba HTTPS scenarios được lưu ở docs/validation/phase08. Docker runtime BLOCKED do thiếu engine; cloud deployment NOT_COMPLETED. Các số này là software verification, không phải accuracy của hệ y tế.

## C. Lệnh vận hành và handoff

```powershell
python -m alembic upgrade head
python scripts/bootstrap_demo.py
npm --prefix frontend run build
python scripts/demo_host.py status
docker compose --env-file .env.compose config --quiet
docker compose --env-file .env.compose up --build --wait
```
Lệnh bootstrap thay đổi schema/graph idempotently và kiểm loaders; chỉ chạy vào database mình có quyền quản lý. Lệnh Compose cuối hiện chưa thành công trên host này. Không đưa secrets vào terminal trình chiếu.

## D. Kịch bản và phản biện

### Demo 2 phút

## Chuẩn bị trước, không tính vào hai phút

Mở URL trong [deployment](../deployment.md), đăng nhập `demo` với password `.env.demo`; tuyệt đối không chiếu file đó. Kiểm readiness, warm một câu hỏi; mở sẵn run thực đã lưu trong [public_demo.json](../validation/phase08/public_demo.json). Máy, BE, PostgreSQL, Neo4j và tunnel phải chạy. Nếu mất internet, dùng native web và nói rõ đang demo local; nếu đọc lại run thì nói rõ là run đã thực thi, không gọi là live.

## Kịch bản nói và thao tác

| Thời điểm | Thao tác | Lời trình bày |
|---|---|---|
| 0:00–0:15 | Tổng quan; chỉ sơ đồ | “Đây là hệ đa agent hỗ trợ tìm hiểu tiểu đường. DL, KG/RAG, LLM, RL và rules là công cụ của các agent. Hệ thống không chẩn đoán.” |
| 0:15–0:55 | Khảo sát mô phỏng → Điền mẫu → xác nhận SYNTHETIC → Yếu tố nguy cơ → chạy | “Input này do dự án tạo. Prediction chạy checkpoint; Knowledge tìm evidence; RL chọn hành động giáo dục; Education tạo nội dung; Verifier và Safety kiểm trước phát hành.” |
| 0:55–1:15 | Chỉ score/model limitation, citation và link | “Score là đầu ra nghiên cứu chưa hiệu chỉnh. Nội dung đang ở chế độ llm/extractive như UI ghi. Đây là nguồn NIDDK thực được gắn với response.” |
| 1:15–1:35 | Xem hành trình; mở quyết định/metadata cần thiết | “Coordinator ghi lý do gọi từng agent, RL proposed/effective action, hai Safety gates và run ID đã lưu SQL. Đây là trace sau chạy, không phải animation tiến độ giả.” |
| 1:35–1:55 | Hỏi về tiểu đường → demo đổi insulin → gửi | “Yêu cầu đổi liều bị Safety chặn trước khi chạy các agent nghiệp vụ. Không tạo citation để hợp thức hóa một lời khuyên nguy hiểm.” |
| 1:55–2:00 | Chốt tại refusal | “Đóng góp là phối hợp có contracts, kiểm chứng và audit. MLP/RL chưa vượt mọi baseline; triển khai hiện là HTTPS tạm, Docker runtime vẫn chưa nghiệm thu.” |

Nếu câu hỏi đầu chưa xong sau khoảng 25 giây, không nhấn gửi nhiều lần. Chuyển sang tab run đã lưu và nói “Tôi mở lại kết quả của lượt đã chạy để xem đầy đủ trace”; báo thực tế pending/fallback. Không đổi label, metric hoặc nội dung output để khớp lời thoại. Không dành hai phút để cài Docker, train model hoặc mở terminal chứa secrets.

## E. Câu hỏi kỹ thuật chọn lọc



### 1. Vì sao gọi là Multi-Agent, không chỉ pipeline?

Mỗi agent có task/result contract, quyền tool, timeout, mục tiêu và phản ứng riêng; Coordinator xử lý trạng thái/feedback, Verifier reject và Safety veto. Bằng chứng ở definitions/tests và actual trace. Tuy vậy đây là centralized MAS với autonomy giới hạn; agent decomposition không tự chứng minh tốt hơn workflow trực tiếp.

### 2. Các agent có cần là các LLM khác nhau không?

Không. Prediction là learned classifier, Knowledge là retrieval, RL là policy, Safety là rules. Education và Verifier gọi cùng provider bằng role/call khác nhau. Không có sáu foundation models hoặc sáu process riêng.

### 3. Coordinator làm gì?

Tạo run state, chọn agent theo input, dispatch typed task, kiểm Result, quản lý deadlines/budgets, retry/repair, lặp publication admission, gọi hai Safety gates và trả snapshot để transaction commit. Nó không dùng prompt để cấp thêm tool permissions.

### 4. Điều gì chứng minh agent phối hợp thật?

POST thật tạo correlated messages/events, có actual model/evidence/action/verification/safety output; GET đọc lại cùng run/trace từ SQL. Evidence yếu dẫn tới retry; unsafe insulin khiến business agents SKIPPED. UI không tạo các kết quả này.

### 5. Tại sao cần DL trong khi LR tốt hơn?

DL đáp ứng thành phần phân loại có huấn luyện của đề tài và cho một serving tool để nghiên cứu phối hợp. Trên split này LR có accuracy/F1 cao hơn; không có lý do khoa học ép MLP phải thắng. Kiến trúc agent tách model nên có thể so/đổi model bằng nghiên cứu versioned sau này, không đổi lén trong demo.

### 6. Model đã train chưa? LLM đã train chưa?

MLP và Q-policy đã train bằng notebook thực. Encoder/reranker dùng pretrained weights. LLM dùng Groq inference API, không tự train/fine-tune. Không gọi việc viết prompt hoặc nạp corpus là training LLM.

### 7. Dữ liệu Pima có phải synthetic không?

Không, đó là nghiên cứu lịch sử 768 hàng. Chỉ input form demo được dự án soạn synthetic; database case có ràng buộc synthetic=true. Không đưa raw Pima row lên UI làm bệnh nhân demo.

### 8. Vì sao Pima không dùng chẩn đoán người Việt?

Population hạn chế, endpoint lịch sử và single split không xác nhận ngoại suy. Score chưa calibrated và thiếu external clinical validation. MLP còn FN 19/41 positive labels trên test ở threshold 0.5.

### 9. Chống data leakage thế nào?

Split stratified seed 42 trước fit preprocessing, median/scaler chỉ fit train, validation chọn epoch, test đo cuối. Không SMOTE/tune threshold trên test. Thiếu patient identifiers nên không khẳng định person-level independence.

### 10. Vì sao epoch 24 nhưng lịch sử có 44 epochs?

Epoch 24 cho validation loss nhỏ nhất; patience 20 dẫn tới dừng ở 44. Serving load checkpoint tốt nhất, không dùng last epoch hoặc chọn bằng test.

### 11. PR-AUC được tính ra sao?

Dự án dùng average_precision_score; không phải trapezoidal area của PR curve. Cần ghi định nghĩa khi so kết quả. Accuracy, recall, F1 và ROC-AUC có ý nghĩa khác nhau.

### 12. Graph có gì ngoài các vector?

Source/evidence/topic/concept/assertion nodes và các relation có supporting quote; 11 assertions curated trong corpus hiện hành. Nó không suy ra causal relations từ Pima. Query được giới hạn, không cho LLM chạy Cypher tùy ý.

### 13. Neo4j có thật sự được dùng trong retrieval không?

Có, candidate reads gắn corpus release. Graph unavailable làm Knowledge UNAVAILABLE và không trả citation, được kiểm bằng fault API. Local embeddings không được giả làm graph access thành công.

### 14. URL đúng có đủ chứng minh câu trả lời đúng không?

Không. Cần đúng source/quote, relevance với câu hỏi và claim entailment. Provenance 1.0 là integrity, không phải medical accuracy. Verifier cũng fallible, nhất là khi author/reviewer cùng provider.

### 15. RAG có hoàn toàn ngăn hallucination không?

Không. Retrieval có thể sai, nguồn hẹp, LLM có thể suy diễn vượt quote. Hệ thống thêm deterministic admission, separate review và Safety/fallback; chưa có chứng nhận hoặc expert clinical benchmark.

### 16. Tại sao không train LLM riêng từ 449 chunks?

Đó là corpus tham khảo, không phải bộ SFT đủ nhãn chất lượng/expected refusal. Train lớn tốn tài nguyên và không tự bảo đảm bám nguồn. Hiện dùng pretrained API với retrieval và evaluation rõ sẽ phù hợp phạm vi hơn.

### 17. RL học điều gì?

Ưu tiên next educational action trong simulator hữu hạn theo reward proxy: kiến thức/engagement/evidence và ngân sách. Không học liều insulin hoặc tối ưu outcome sức khỏe. Runtime chọn một action/run, không học online.

### 18. State/action/reward cụ thể?

State có 7 biến, 7938 states; sáu action giáo dục. Reward: −0.2 step, gains kiến thức/engagement, penalty unsupported/repeat, completion bonus và −20 unsafe-context action. Các thông số là thiết kế simulator; xem rl_mdp và source reward.

### 19. Vì sao runtime knowledge/engagement lại giả lập?

Chưa có phép đo người dùng thật hoặc dữ liệu tương tác. Vì vậy context được gắn SIMULATED_DEFAULTS_NOT_MEASURED. Không suy ra “người này ít hiểu” từ tuổi/giới/score; không nhận hiệu quả giáo dục cá nhân hóa đã được chứng minh.

### 20. Q-learning có vượt rules không?

Chưa. Saved serving reward Q 4.276 vs rules 4.311; completion 0.97 vs 0.983333 trên cùng 300 held-out seeds. Báo kết quả âm thay vì đổi reward/baseline sau khi xem test.

### 21. Rule-based khác RL và ưu tiên ra sao?

Rules trực tiếp mã hóa constraints; Q cập nhật từ transitions/rewards. Action masks và Safety là ràng buộc bắt buộc, có thể veto mọi learned recommendation. Q-value không cấp quyền điều trị.

### 22. Khi Groq lỗi, có bịa lời đáp hay citation không?

Không. Nếu còn admitted evidence thì exact-source fallback có nhãn extractive; không có thì clarification/withheld. Missing auth/rate/schema/timeout có code sanitize. Mode hiển thị đúng, không gọi fallback là LLM generation.

### 23. LLM benchmark 100% nghĩa gì?

Không có 100% clinical accuracy. Sáu câu: ba LLM outputs và cả ba được automated verifier chấp nhận; hai clarification và một extractive fallback. Coverage 3/6, acceptance conditional 3/3. Mẫu nhỏ, reviewer cùng provider và không có medical expert review.

### 24. MAS có tốt hơn baseline không?

Saved offline completion cao hơn nhưng có retry/repair budget cao hơn; evidence relevance có điều kiện lại thấp hơn và latency cao hơn. Không tách được hiệu ứng decomposition. Cần matched-budget/ablation và human grounding evaluation trước superiority claim.

### 25. Timeout có kill được mọi computation không?

Không. asyncio task budget xử lý async timeout nhưng native/thread blocking có thể tiếp tục. Warmup tách trước budget; graph/HTTP có timeout riêng. Không nhận hard realtime guarantee.

### 26. Tại sao HTTP 201 sau commit?

Để phản hồi “đã tạo run” chỉ xảy ra khi prediction/snapshot/events được lưu. DB failure rollback và 503 sanitized. GET readback qua new request xác nhận durable storage; in-memory status không đủ.

### 27. Làm sao không lẫn concurrent workflows?

Run-local state/registry/messages/budget, UUID correlation và unique event sequence theo run. Shared models/policy readonly với khóa; tests concurrent creation/readback kiểm tra correlation. Chưa benchmark tải production.

### 28. Có deploy cloud chưa?

Chưa. URL thật là Quick Tunnel HTTPS đến máy cá nhân, có gateway password; cloud hosting NOT_COMPLETED. Chỉ link frontend không chứng minh full backend/DB đã chạy trên cloud.

### 29. Docker đã chạy thành công chưa?

Chưa trên máy này. Compose config parse được nhưng engine không có; `up` lỗi docker_engine pipe. Cần host Docker chạy build/start/health/workflows/restart/volume persistence rồi mới đóng acceptance.

### 30. Nếu thầy yêu cầu xác nhận hoàn thành 100%?

Trình audit và tiêu chí cụ thể: các khối nghiệp vụ có code/demo, report có số liệu, nhưng gate Docker còn thiếu và nghiên cứu chưa clinical validated. Không ký 100% khi tiêu chí runtime chưa kiểm chứng; trạng thái Phase 08 hiện BLOCKED, demo native/HTTPS vẫn dùng được.

### 31. Điều gì cần cải thiện đầu tiên?

Đóng Docker runtime gate, đo LLM bilingual coverage/grounding có reviewer độc lập, MAS matched-budget; sau đó CV/calibration DL và simulator realism. Không tăng số agent/epoch để thay cho bằng chứng.

### 32. Quyền dữ liệu và reproducibility xử lý ra sao?

Pima mirror được pin hash nhưng license redistribution chưa xác minh; raw/fitted artifacts ignored. NIDDK snapshots giới hạn public educational text có provenance. Người tái lập dùng trusted bundle hoặc chạy prepare/train, ghi versions/hashes; không giả có remote repo hoặc checkpoints trong Git.
