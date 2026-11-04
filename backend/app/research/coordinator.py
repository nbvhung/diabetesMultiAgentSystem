"""Bounded multi-agent feedback workflow with mandatory independent publication gates."""
import asyncio,time
from uuid import uuid4
from backend.app.rl.mdp import ACTIONS
from .schemas import *
from . import safety
from .grounding import candidate_digest,extractive,publication_errors
from .retrieval import query_topics,rewrite_query
from .config import research_settings


class Coordinator:
    def __init__(self,registry,corpus):self.registry=registry;self.corpus=corpus
    async def run(self,request):
        # Everything mutable is request-local, including budgets and retry state.
        run_id=uuid4();trace=[];warnings=[];decisions=[];rounds=0;proof=None;mode='clarification'
        results={name:Result(agent_id=name,status=AgentStatus.NOT_STARTED) for name in AgentId}
        deadline=time.monotonic()+85
        def event(name,status,reason,**fields):
            trace.append(Event(sequence=len(trace)+1,run_id=run_id,agent_id=name,status=status,reason=reason,**fields))
        def skip(name,reason):
            if results[name].status==AgentStatus.NOT_STARTED:
                results[name]=Result(agent_id=name,status=AgentStatus.SKIPPED);event(name,AgentStatus.SKIPPED,reason)
        def summary(payload):
            if isinstance(payload,PredictionTask):return {'contract':'PredictionTask','assessment_feature_count':8,'raw_values':'WITHHELD'}
            if isinstance(payload,KnowledgeTask):return {'contract':'KnowledgeTask','question_chars':len(payload.question),'query_chars':len(payload.query),'attempt':payload.attempt}
            if isinstance(payload,RLTask):return {'contract':'RLTask','prediction_present':payload.prediction is not None,'evidence_count':len(payload.evidence),'context':'SIMULATED_DEFAULTS'}
            if isinstance(payload,EducationTask):return {'contract':'EducationTask','question_chars':len(payload.question or ''),'evidence_count':len(payload.evidence),'language':payload.language,'feedback_codes':payload.feedback}
            if isinstance(payload,VerifierTask):return {'contract':'VerifierTask','candidate_chars':len(payload.candidate.text),'claim_count':len(payload.candidate.claims),'evidence_count':len(payload.evidence)}
            return {'contract':'SafetyTask','stage':payload.stage,'question_chars':len(payload.question or ''),'candidate_chars':len(payload.candidate)}
        def output_summary(output):
            if isinstance(output,KnowledgeOutput):return {'evidence_count':len(output.evidence),'source_count':len({e.source_id for e in output.evidence}),'coverage':output.coverage,'adequate':output.adequate,'semantic_available':output.semantic_available,'retrieval_method':output.retrieval_method}
            if isinstance(output,EducationOutput):return {'generation_mode':output.generation_mode,'llm_status':output.llm_status,'llm_model':output.llm_model,'claim_count':len(output.claims),'citation_count':len(output.evidence_ids),'provider_error':output.provider_error,'input_tokens':output.input_tokens,'output_tokens':output.output_tokens,'proposed_action':output.proposed_action,'effective_action':output.effective_action,'override_reason':output.override_reason}
            if isinstance(output,VerifierOutput):return {'verified':output.verified,'mode':output.mode,'checked_claims':output.checked_claims,'reason_codes':output.reason_codes,'input_tokens':output.input_tokens,'output_tokens':output.output_tokens}
            if isinstance(output,PredictionResult):return {'model_version':output.model_version,'score':output.score,'predicted_class':output.predicted_class,'persisted':output.persisted_record_id is not None}
            if isinstance(output,RLDecision):return {'action':output.action,'policy_version':output.policy_version,'decision_source':output.decision_source}
            if isinstance(output,SafetyDecision):return {'decision':output.decision,'rule_ids':output.rule_ids,'stage':output.stage}
            return {}
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
            return result
        async def check_safety(task):
            result=await dispatch(AgentId.safety,task)
            try:
                if not isinstance(result.output,SafetyDecision) or result.output.stage!=task.stage:raise ValueError('Safety missing')
                mandatory=safety.evaluate(task);decision=result.output
                order={'ALLOW':0,'ALLOW_WITH_WARNING':1,'REQUEST_CLARIFICATION':2,'BLOCK':3,'ESCALATE':4}
                if order[mandatory.decision]>order[decision.decision]:decision=mandatory
            except Exception:
                decision=SafetyDecision(allowed=False,decision='BLOCK',severity='critical',rule_ids=['SYS01_SAFETY_FAILURE'],reason='Safety unavailable; content withheld',checked_content='Raw content not retained',stage=task.stage)
            decisions.append(decision)
            if result.status==AgentStatus.COMPLETED:results[AgentId.safety]=Result(agent_id=AgentId.safety,status=AgentStatus.COMPLETED,output=decision)
            event(AgentId.safety,AgentStatus.COMPLETED,'SAFETY_GATE_'+task.stage.upper(),rule_ids=decision.rule_ids,safety_stage=task.stage,safety_decision=decision.decision)
            if decision.decision!='ALLOW':warnings.extend(decision.rule_ids)
            return decision
        def finish(status,text,evidence,generation,grounding=None):
            for name in AgentId:skip(name,'NO_REMAINING_TASK')
            if status in (WorkflowStatus.BLOCKED,WorkflowStatus.FAILED):
                for name in (AgentId.education,AgentId.knowledge,AgentId.verifier):
                    previous=results[name]
                    if previous.status==AgentStatus.COMPLETED:
                        # Do not serialize rejected drafts, forged citations or free prose.
                        if name==AgentId.education:results[name]=Result(agent_id=name,status=AgentStatus.COMPLETED,output=EducationOutput(text='[WITHHELD_BY_SAFETY]',evidence_ids=[],generation_mode='withheld',llm_status='not_called'))
                        elif name==AgentId.knowledge:results[name]=Result(agent_id=name,status=AgentStatus.COMPLETED,output=previous.output.model_copy(update={'evidence':[]}))
                if results[AgentId.rl].output:
                    results[AgentId.rl]=Result(agent_id=AgentId.rl,status=AgentStatus.COMPLETED,output=results[AgentId.rl].output.model_copy(update={'action':'WITHHELD_BY_SAFETY','state':{}}))
                for item in trace:
                    if item.action:item.action='WITHHELD_BY_SAFETY'
                    if 'action' in item.output_summary:item.output_summary['action']='WITHHELD_BY_SAFETY'
            event(None,status,'WORKFLOW_TRANSITION')
            try:version=self.corpus.manifest['dataset_version']
            except AttributeError:version=None
            return WorkflowResponse(run_id=run_id,status=status,response=text,evidence=evidence,agent_results=results,agent_trace=trace,safety_decisions=decisions,warnings=list(dict.fromkeys(warnings)),limitations=['Research/education only; no diagnosis or treatment changes.','DL score is uncalibrated; RL context/reward is simulator-only.','LLM semantic review is fallible, not clinical certification.','Evidence is limited to registered versioned NIDDK diabetes education sources.'],generation_mode=generation,grounding=grounding,retrieval_rounds=rounds,corpus_version=version)
        event(None,WorkflowStatus.RUNNING,'WORKFLOW_TRANSITION')
        pre=await check_safety(SafetyTask(stage='input',question=request.question,assessment=request.assessment.model_dump() if request.assessment else None))
        if not pre.allowed:
            for name in AgentId:
                if name!=AgentId.safety:skip(name,'SAFETY_PREFLIGHT_DENIED')
            text=safety.safe_message(pre);post=await check_safety(SafetyTask(stage='output',question=request.question,candidate=text,abstention=True))
            failed=any('SYS01_SAFETY_FAILURE' in d.rule_ids for d in decisions)
            return finish(WorkflowStatus.FAILED if failed else WorkflowStatus.BLOCKED,safety.FAIL_CLOSED if failed else text,[],'withheld')
        prediction=None;evidence=[];decision=None
        if request.assessment:
            event(None,WorkflowStatus.RUNNING,'PREDICT_SYNTHETIC_ASSESSMENT')
            result=await dispatch(AgentId.prediction,PredictionTask(assessment=request.assessment))
            if result.status==AgentStatus.COMPLETED:prediction=result.output;warnings.extend(prediction.warnings)
        else:skip(AgentId.prediction,'NO_ASSESSMENT')
        if request.question:
            query=request.question
            for attempt in range(1,research_settings.diabetes_max_retrieval_rounds+1):
                rounds=attempt
                result=await dispatch(AgentId.knowledge,KnowledgeTask(question=request.question,query=query,attempt=attempt),attempt)
                if result.status!=AgentStatus.COMPLETED:break
                output=result.output
                if output.adequate:
                    evidence=output.evidence
                    if not output.semantic_available:warnings.append('SEMANTIC_MODEL_UNAVAILABLE_LEXICAL_FALLBACK')
                    if not output.reranker_available:warnings.append('RERANKER_UNAVAILABLE_BIENCODER_FALLBACK')
                    event(None,WorkflowStatus.RUNNING,'EVIDENCE_ADEQUATE',output_summary={'evidence_count':len(evidence),'coverage':output.coverage});break
                if attempt<research_settings.diabetes_max_retrieval_rounds:
                    query=rewrite_query(request.question,output.query_topics,retry=True)
                    event(None,WorkflowStatus.RUNNING,'RETRIEVE_AGAIN_WEAK_EVIDENCE',attempt=2,output_summary={'previous_coverage':output.coverage})
            if not evidence:warnings.append('INSUFFICIENT_RELEVANT_EVIDENCE');event(None,WorkflowStatus.RUNNING,'REQUEST_CLARIFICATION_NO_EVIDENCE')
        else:skip(AgentId.knowledge,'NO_QUESTION')
        result=await dispatch(AgentId.rl,RLTask(prediction=prediction,evidence=evidence))
        if result.status==AgentStatus.COMPLETED:
            decision=result.output
            if decision.decision_source=='fallback':warnings.append('RL_POLICY_FALLBACK')
        if 'RL_ACTION_NOT_ALLOWED' in result.errors:
            skip(AgentId.education,'INVALID_RL_ACTION');skip(AgentId.verifier,'INVALID_RL_ACTION')
            post=await check_safety(SafetyTask(stage='output',question=request.question,candidate=safety.FAIL_CLOSED,abstention=True,action='INVALID_RL_ACTION'))
            return finish(WorkflowStatus.BLOCKED,safety.safe_message(post),[],'withheld')
        feedback=[];candidate=None
        for attempt in (1,2):
            result=await dispatch(AgentId.education,EducationTask(question=request.question,language=request.language,evidence=evidence,decision=decision,feedback=feedback),attempt)
            if result.status!=AgentStatus.COMPLETED:break
            candidate=result.output
            reviewed=await dispatch(AgentId.verifier,VerifierTask(question=request.question,candidate=candidate,evidence=evidence),attempt)
            if reviewed.status==AgentStatus.COMPLETED and reviewed.output.verified:
                proof=reviewed.output;break
            feedback=reviewed.output.reason_codes if reviewed.output else ['VERIFIER_UNAVAILABLE']
            warnings.append('CANDIDATE_WITHHELD_BY_VERIFIER')
            # Erase unverified draft before repair; only codes/counters enter trace.
            results[AgentId.education]=Result(agent_id=AgentId.education,status=AgentStatus.FAILED,errors=['UNVERIFIED_DRAFT_WITHHELD'])
            candidate=None
            event(None,WorkflowStatus.RUNNING,'RECOMPOSE_AFTER_VERIFIER_REJECTION' if attempt<2 else 'DRAFT_REPAIR_BUDGET_EXHAUSTED',attempt=attempt+1,output_summary={'reason_codes':feedback})
            if time.monotonic()>deadline-15:break
        if proof is None:
            warnings.append('VERIFIED_EXTRACTIVE_FALLBACK')
            candidate=extractive(evidence,request.language,error='LLM_DRAFT_NOT_VERIFIED',action=decision.action if decision else None)
            results[AgentId.education]=Result(agent_id=AgentId.education,status=AgentStatus.COMPLETED,output=candidate)
            event(AgentId.education,AgentStatus.COMPLETED,'COORDINATOR_EXTRACTIVE_FALLBACK',output_summary=output_summary(candidate))
            reviewed=await dispatch(AgentId.verifier,VerifierTask(question=request.question,candidate=candidate,evidence=evidence),3)
            proof=reviewed.output if reviewed.status==AgentStatus.COMPLETED else None
        if candidate.provider_error:warnings.append(candidate.provider_error)
        if proof and proof.verified and proof.candidate_sha256==candidate_digest(candidate):
            selected=[e for e in evidence if e.evidence_id in candidate.evidence_ids]
        else:selected=[]
        try:trusted=all(self.corpus.admits(e) for e in selected)
        except Exception:trusted=False
        verified=bool(proof and proof.verified and proof.candidate_sha256==candidate_digest(candidate))
        try:
            errors=publication_errors(candidate,selected,self.corpus)
            if errors:verified=False;warnings.extend(errors)
            if candidate.generation_mode=='llm' and proof.mode!='independent_llm':verified=False
        except Exception:verified=False;trusted=False
        post=await check_safety(SafetyTask(stage='output',question=request.question,candidate=candidate.text if verified else safety.FAIL_CLOSED,grounded=verified and bool(selected),abstention=verified and candidate.generation_mode=='clarification',evidence_ids=[e.evidence_id for e in selected],cited_ids=candidate.evidence_ids,trusted_evidence=trusted and verified,prediction_present=prediction is not None,knowledge_available=bool(evidence),action=decision.action if decision else ''))
        if not post.allowed or not verified:
            failed='SYS01_SAFETY_FAILURE' in post.rule_ids
            return finish(WorkflowStatus.FAILED if failed else WorkflowStatus.BLOCKED,safety.safe_message(post),[],'withheld')
        mode=candidate.generation_mode
        return finish(WorkflowStatus.DEGRADED if warnings or mode!='llm' else WorkflowStatus.COMPLETED,candidate.text,selected,mode,proof)
