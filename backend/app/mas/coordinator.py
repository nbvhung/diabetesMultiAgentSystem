"""Sequential, request-local orchestration. Only validated outputs flow downstream."""
import asyncio
import logging
from backend.app.mas.registry import AgentRegistry, build_runtime_registry
from backend.app.mas.state import record, transition_agent, transition_workflow
from backend.app.mas.agents.runtime import ABSTENTION, REFUSAL, FAIL_CLOSED
from backend.app.schemas.contracts import AgentName, KnowledgeOutput, PredictionResult, RLDecision, EducationOutput, SafetyDecision
from backend.app.schemas.safety import SafetyDecision as PolicySafetyDecision
from backend.app.rules.engine import Context, RuleEngine
from backend.app.schemas.runtime import (RunInput, AgentMessage, AgentResult, AgentStatus, WorkflowState,
    WorkflowResponse, WorkflowStatus, PredictionTask, KnowledgeTask, RLTask, EducationTask, SafetyTask)

logger = logging.getLogger(__name__)


class Coordinator:
    def __init__(self, registry: AgentRegistry | None = None, persistent: bool = False):
        self.persistent = persistent
        self.registry = registry if registry is not None else build_runtime_registry()

    def unavailable_or_skip(self, state, name, status, reason):
        current = state.agent_results[name]
        result = AgentResult(agent_id=name, status=status, implementation=current.implementation,
            errors=[reason] if status == AgentStatus.UNAVAILABLE else [])
        transition_agent(state, result, reason)
        if status == AgentStatus.UNAVAILABLE:
            state.warnings.append(f"{name.value}: {reason}")

    async def dispatch(self, state: WorkflowState, name: AgentName, payload) -> AgentResult:
        if name != AgentName.safety and (state.status != WorkflowStatus.RUNNING or not any(d.stage == 'input' and d.allowed for d in state.safety_decisions) or any(d.stage == 'output' or not d.allowed for d in state.safety_decisions)):
            raise ValueError('SAFETY_PREFLIGHT_REQUIRED')
        agent = self.registry.get(name)
        if agent is None:
            self.unavailable_or_skip(state, name, AgentStatus.UNAVAILABLE, "AGENT_UNREGISTERED")
            return state.agent_results[name]
        message = AgentMessage(run_id=state.run_id, recipient=name, payload=payload)
        transition_agent(state, AgentResult(agent_id=name, status=AgentStatus.RUNNING,
            implementation=agent.definition.implementation), "TASK_DISPATCHED", message.message_id, safety_stage=getattr(payload,"stage",None))
        try:
            raw = await asyncio.wait_for(agent.execute(message), timeout=agent.definition.timeout_seconds)
            result = AgentResult.model_validate(raw.model_dump())
            if result.agent_id != name or result.implementation != agent.definition.implementation:
                raise ValueError("Result identity does not match registered agent")
            from backend.app.rl.mdp import ACTIONS
            if name == AgentName.rl and result.status == AgentStatus.COMPLETED and result.output.action not in ACTIONS:
                result = AgentResult(agent_id=name,status=AgentStatus.FAILED,implementation=agent.definition.implementation,errors=['RL_ACTION_NOT_ALLOWED'])
            if result.status not in {AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.UNAVAILABLE}:
                raise ValueError("Agent must return terminal execution status")
        except TimeoutError:
            result = AgentResult(agent_id=name, status=AgentStatus.FAILED,
                implementation=agent.definition.implementation, errors=["AGENT_TIMEOUT"])
        except Exception:
            # Never expose exception text, input, output or credentials in trace/log.
            logger.error("agent_execution_failed run_id=%s agent=%s", state.run_id, name.value)
            result = AgentResult(agent_id=name, status=AgentStatus.FAILED,
                implementation=agent.definition.implementation, errors=["AGENT_EXCEPTION_OR_INVALID_RESULT"])
        transition_agent(state, result, result.errors[0] if result.errors else "TASK_COMPLETED", message.message_id)
        if name == AgentName.safety:
            state.trace[-1].safety_stage = payload.stage
            if isinstance(result.output, PolicySafetyDecision):
                state.trace[-1].rule_ids = result.output.rule_ids
                state.trace[-1].safety_decision = result.output.decision
        if name == AgentName.rl and result.status == AgentStatus.COMPLETED:
            state.trace[-1].policy_version=result.output.policy_version
            state.trace[-1].action=result.output.action
            state.trace[-1].decision_source=result.output.decision_source
            if result.output.decision_source=='fallback':state.warnings.append('RL_POLICY_FALLBACK:'+str(result.output.state.get('decision_reason','UNSPECIFIED')))
        if name == AgentName.education and result.status == AgentStatus.COMPLETED:
            proposed=getattr(result.output,'proposed_action',None)
            effective=getattr(result.output,'effective_action',None)
            override=getattr(result.output,'override_reason',None)
            state.trace[-1].proposed_action=proposed
            state.trace[-1].effective_action=effective
            state.trace[-1].action_override_reason=override
            if proposed is not None:
                for event in state.trace:
                    if event.agent_id==AgentName.rl and event.policy_version:
                        event.proposed_action=proposed;event.effective_action=effective;event.action_override_reason=override
        if name == AgentName.knowledge and result.status == AgentStatus.COMPLETED and not result.output.evidence:
            state.trace[-1].reason = 'NO_EVIDENCE'
            state.warnings.append('NO_EVIDENCE')
        if name == AgentName.prediction and result.status == AgentStatus.COMPLETED:
            state.trace[-1].model_version = result.output.model_version
            state.trace[-1].inference_latency_ms = getattr(result.output, 'inference_latency_ms', None)
            state.warnings.extend(getattr(result.output, 'warnings', []))
        if result.status != AgentStatus.COMPLETED:
            state.warnings.append(f"{name.value}: {','.join(result.errors) or result.status.value}")
            state.errors.extend(result.errors)
        logger.info("agent_result run_id=%s agent=%s status=%s", state.run_id, name.value, result.status.value)
        return result

    async def run(self, request: RunInput) -> WorkflowResponse:
        # Deep copy guards caller mutation; no state kept on the Coordinator instance.
        state = WorkflowState(request=request.model_copy(deep=True))
        for name in AgentName:
            agent = self.registry.get(name)
            state.agent_results[name] = AgentResult(agent_id=name, status=AgentStatus.NOT_STARTED,
                implementation=agent.definition.implementation if agent else "stub")
        transition_workflow(state, WorkflowStatus.RUNNING)
        pre = await self.check_safety(state, SafetyTask(stage='input',question=state.request.question,
            assessment=state.request.assessment.model_dump() if state.request.assessment else None))
        if not pre.allowed:
            for name in (AgentName.prediction, AgentName.knowledge, AgentName.rl, AgentName.education):
                self.unavailable_or_skip(state,name,AgentStatus.SKIPPED,'SAFETY_PREFLIGHT_DENIED')
            text = self.safe_message(pre)
            post = await self.check_safety(state,SafetyTask(stage='output',question=state.request.question,candidate=text,abstention=True))
            status = WorkflowStatus.FAILED if 'SYS01_SAFETY_FAILURE' in pre.rule_ids else WorkflowStatus.BLOCKED
            if 'SYS01_SAFETY_FAILURE' in post.rule_ids: status,text=WorkflowStatus.FAILED,FAIL_CLOSED
            return self.finish(state,status,text,[])
        prediction = None
        evidence = []
        decision = None
        if state.request.assessment is not None:
            result = await self.dispatch(state, AgentName.prediction, PredictionTask(assessment=state.request.assessment))
            if result.status == AgentStatus.COMPLETED and isinstance(result.output, PredictionResult):
                prediction = result.output
        else:
            self.unavailable_or_skip(state, AgentName.prediction, AgentStatus.SKIPPED, "NO_ASSESSMENT")
        if state.request.question is not None:
            result = await self.dispatch(state, AgentName.knowledge, KnowledgeTask(question=state.request.question))
            if result.status == AgentStatus.COMPLETED and isinstance(result.output, KnowledgeOutput):
                evidence = result.output.evidence
        else:
            self.unavailable_or_skip(state, AgentName.knowledge, AgentStatus.SKIPPED, "NO_QUESTION")
        rl = self.registry.get(AgentName.rl)
        if rl is None or not rl.definition.available:
            self.unavailable_or_skip(state, AgentName.rl, AgentStatus.UNAVAILABLE, "NO_COMPATIBLE_POLICY")
        elif prediction is None and not evidence and rl.definition.implementation != 'integrated':
            self.unavailable_or_skip(state, AgentName.rl, AgentStatus.SKIPPED, "NO_VALID_POLICY_CONTEXT")
        else:
            result = await self.dispatch(state, AgentName.rl, RLTask(prediction=prediction, evidence=evidence, safety_status='normal' if pre.decision=='ALLOW' else 'restricted'))
            if result.status == AgentStatus.COMPLETED and isinstance(result.output, RLDecision):
                decision = result.output
        if 'RL_ACTION_NOT_ALLOWED' in state.agent_results[AgentName.rl].errors:
            self.unavailable_or_skip(state,AgentName.education,AgentStatus.SKIPPED,'INVALID_RL_ACTION')
            post=await self.check_safety(state,SafetyTask(stage='output',question=state.request.question,candidate=FAIL_CLOSED,abstention=True,action='INVALID_RL_ACTION'))
            return self.finish(state,WorkflowStatus.FAILED if 'SYS01_SAFETY_FAILURE' in post.rule_ids else WorkflowStatus.BLOCKED,self.safe_message(post),[])
        education = await self.dispatch(state, AgentName.education, EducationTask(question=state.request.question,
            prediction=prediction, evidence=evidence, decision=decision, warnings=list(state.warnings)))
        candidate = ABSTENTION
        if education.status == AgentStatus.COMPLETED and isinstance(education.output, EducationOutput):
            # Unsupported citations are a contract failure; never deliver the candidate.
            if not set(education.output.evidence_ids) <= {item.evidence_id for item in evidence}:
                state.warnings.append("UNSUPPORTED_EDUCATION_CITATION")
                candidate = FAIL_CLOSED
            else:
                candidate = education.output.text
        else:
            state.warnings.append("EDUCATION_FALLBACK_ABSTENTION")
        from backend.app.knowledge.store import validate_url, safe_text, documents
        trusted = True
        try: approved = {c['id']:c for c in documents()} if evidence else {}
        except Exception: approved = {}; trusted = False
        for item in evidence:
            source = approved.get(item.evidence_id)
            if source is None or source['text'] != item.excerpt or source['url'] != str(item.source_url) or source['title'] != item.source_title or source['publisher'] != item.publisher or source['section'] != item.section:
                trusted = False
            try: validate_url(str(item.source_url))
            except ValueError: trusted = False
            if not safe_text(item.excerpt): trusted = False
        cited = education.output.evidence_ids if education.status == AgentStatus.COMPLETED else []
        rendered = 'Retrieved NIDDK educational excerpts (not diagnosis or treatment instructions):\n'+'\n'.join(
            f'[{e.evidence_id}] {e.excerpt} (Source: {e.source_url}; section: {e.section})' for e in evidence if e.evidence_id in cited)
        from backend.app.rl.rendering import render_action, TEXT
        from backend.app.rl.mdp import ACTIONS
        selected_template = None
        if decision is not None and decision.action in ACTIONS:
            selected_template, _ = render_action(decision.action,[e for e in evidence if e.evidence_id in cited])
        abstention = candidate in (ABSTENTION, FAIL_CLOSED) or candidate == ABSTENTION + ' Không có kết quả mô hình để diễn giải.'
        post = await self.check_safety(state,SafetyTask(stage='output',question=state.request.question,candidate=candidate,
            evidence_ids=[e.evidence_id for e in evidence],cited_ids=cited,trusted_evidence=trusted,
            grounded=bool(evidence) and candidate in (rendered, selected_template),abstention=abstention or candidate in TEXT.values(),
            prediction_present=prediction is not None,knowledge_available=state.agent_results[AgentName.knowledge].status==AgentStatus.COMPLETED,
            action=decision.action if decision else ''))
        if not post.allowed:
            status = WorkflowStatus.FAILED if 'SYS01_SAFETY_FAILURE' in post.rule_ids else WorkflowStatus.BLOCKED
            return self.finish(state,status,self.safe_message(post),[])
        if 'UNSUPPORTED_EDUCATION_CITATION' in state.warnings:
            return self.finish(state,WorkflowStatus.FAILED,FAIL_CLOSED,[])
        return self.finish(state,WorkflowStatus.DEGRADED if state.warnings else WorkflowStatus.COMPLETED,candidate,evidence)

    async def check_safety(self,state,task):
        try:
            result = await self.dispatch(state,AgentName.safety,task)
            if result.status != AgentStatus.COMPLETED or not isinstance(result.output,PolicySafetyDecision):
                raise ValueError('SAFETY_UNAVAILABLE_OR_INVALID')
            decision = result.output
            if decision.stage != task.stage: raise ValueError('SAFETY_STAGE_MISMATCH')
            # Independently enforce policy on the same typed context: a compromised/replaced
            # Safety implementation cannot downgrade BLOCK/ESCALATE or enable an old policy.
            context_data={k:v for k,v in task.model_dump().items() if k in Context.__dataclass_fields__}
            context_data['question']=task.question or ''
            mandatory = RuleEngine().evaluate(Context(**context_data))
            order={'ALLOW':0,'ALLOW_WITH_WARNING':1,'REQUEST_CLARIFICATION':2,'BLOCK':3,'ESCALATE':4}
            if order[mandatory.decision] > order[decision.decision]: decision=mandatory
        except Exception:
            decision=PolicySafetyDecision(allowed=False,decision='BLOCK',severity='critical',rule_ids=['SYS01_SAFETY_FAILURE'],reason='Safety unavailable, invalid or failed; content withheld',checked_content='Raw content not retained',stage=task.stage)
        current=state.agent_results.get(AgentName.safety)
        if current is not None and current.status==AgentStatus.COMPLETED:
            state.agent_results[AgentName.safety]=current.model_copy(update={'output':decision})
        state.safety_decisions.append(decision)
        # Record effective rule IDs, including independent enforcement or failures.
        record(state,'COMPLETED' if 'SYS01_SAFETY_FAILURE' not in decision.rule_ids else 'FAILED','SAFETY_GATE_'+task.stage.upper(),AgentName.safety)
        state.trace[-1].rule_ids=list(decision.rule_ids)
        state.trace[-1].safety_decision=decision.decision
        state.trace[-1].safety_stage=task.stage
        if decision.decision != 'ALLOW':state.warnings.extend(decision.rule_ids)
        return decision

    @staticmethod
    def safe_message(decision):
        if 'SYS01_SAFETY_FAILURE' in decision.rule_ids:return FAIL_CLOSED
        if decision.decision=='ESCALATE':return 'Tình huống được mô tả có thể cần hỗ trợ y tế khẩn cấp. Hãy liên hệ dịch vụ cấp cứu địa phương hoặc tìm trợ giúp y tế ngay; hệ thống dừng tư vấn tự động.'
        if decision.decision=='REQUEST_CLARIFICATION':return 'Không đủ thông tin phù hợp để tiếp tục. Vui lòng làm rõ câu hỏi giáo dục hoặc cung cấp đầy đủ dữ liệu synthetic; hệ thống không suy diễn thông tin còn thiếu.'
        return REFUSAL

    def finish(self,state,status,text,evidence):
        if {d.stage for d in state.safety_decisions} != {'input','output'}:
            raise ValueError('BOTH_SAFETY_GATES_REQUIRED')
        if any(not d.allowed for d in state.safety_decisions) and status not in {WorkflowStatus.BLOCKED,WorkflowStatus.FAILED}:
            raise ValueError('SAFETY_VETO_CANNOT_BE_OVERRIDDEN')
        if status in {WorkflowStatus.BLOCKED,WorkflowStatus.FAILED}:
            edu=state.agent_results[AgentName.education]
            if edu.status==AgentStatus.COMPLETED:
                state.agent_results[AgentName.education]=edu.model_copy(update={'output':EducationOutput(text='[WITHHELD_BY_SAFETY]',evidence_ids=[])})
            know=state.agent_results[AgentName.knowledge]
            if know.status==AgentStatus.COMPLETED:
                state.agent_results[AgentName.knowledge]=know.model_copy(update={'output':KnowledgeOutput(evidence=[])})
            for event in state.trace:
                if event.action:event.action='WITHHELD_BY_SAFETY'
                if event.proposed_action:event.proposed_action='WITHHELD_BY_SAFETY'
                if event.effective_action:event.effective_action='WITHHELD_BY_SAFETY'
                if event.action_override_reason:event.action_override_reason='SAFETY_VETO'
            rl=state.agent_results[AgentName.rl]
            if rl.status==AgentStatus.COMPLETED:
                state.agent_results[AgentName.rl]=rl.model_copy(update={'output':rl.output.model_copy(update={'action':'WITHHELD_BY_SAFETY','state':{}})})
        state.final_response=text
        if not self.persistent:state.warnings.append('IN_MEMORY_STORAGE_NON_DURABLE')
        transition_workflow(state,status)
        return WorkflowResponse(run_id=state.run_id,status=status,agent_results=state.agent_results,response=text,evidence=evidence,agent_trace=state.trace,warnings=state.warnings,
            limitations=['Deterministic safety policy, not clinical diagnosis/triage validation.','Prediction and RL outputs are research/simulator only; no clinical decisions.','Only configured evidence templates/abstentions may be released.'],safety_decisions=state.safety_decisions)
