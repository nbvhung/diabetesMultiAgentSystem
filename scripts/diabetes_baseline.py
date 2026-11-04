"""Same-tool direct workflow reference; no Coordinator/agent/registry dispatch."""
from uuid import uuid4
from backend.app.research.schemas import SafetyTask,RLDecision
from backend.app.research.safety import evaluate,safe_message,FAIL_CLOSED
from backend.app.research.grounding import compose,verify_candidate,extractive
from backend.app.ml.serving import ModelUnavailable
from backend.app.rl.mdp import ACTIONS
from backend.app.knowledge.store import KnowledgeUnavailable


async def run_single(request,state,services,repository):
    run_id=uuid4();pre=evaluate(SafetyTask(stage='input',question=request.question,assessment=request.assessment.model_dump() if request.assessment else None))
    if not pre.allowed:
        text=safe_message(pre);post=evaluate(SafetyTask(stage='output',question=request.question,candidate=text,abstention=True))
        return {'status':'BLOCKED','response':text,'evidence':[],'generation_mode':'withheld','safety':[pre,post],'prediction':None,'warnings':[],'retrieval_rounds':0,'grounding':None}
    prediction=None;evidence=[];warnings=[];rounds=0
    if request.assessment:
        try:prediction=repository.persist_prediction(run_id,request.assessment,state.model_service.predict(request.assessment),state.model_service)
        except ModelUnavailable:warnings.append('MODEL_UNAVAILABLE')
    if request.question:
        rounds=1
        try:
            output=services.retriever.search(request.question)
            if output.adequate:evidence=output.evidence
            else:warnings.append('INSUFFICIENT_RELEVANT_EVIDENCE')
            if not output.semantic_available:warnings.append('SEMANTIC_MODEL_UNAVAILABLE_LEXICAL_FALLBACK')
        except KnowledgeUnavailable:warnings.append('NEO4J_UNAVAILABLE')
    band=0 if prediction is None else 1 if prediction.score<.5 else 2
    action,source,reason,version=state.policy_service.choose((band,1,1,min(2,len(evidence)),0,6,6))
    if action not in ACTIONS:raise ValueError('Invalid baseline policy action')
    if source=='fallback':warnings.append('RL_POLICY_FALLBACK')
    decision=RLDecision(state={},action=action,decision_source=source,policy_version=version)
    candidate=await compose(request.question,request.language,evidence,decision,services.llm)
    proof=await verify_candidate(candidate,evidence,services.corpus,services.llm,request.question)
    if not proof.verified:
        candidate=extractive(evidence,request.language,error='LLM_DRAFT_NOT_VERIFIED',action=action)
        proof=await verify_candidate(candidate,evidence,services.corpus,services.llm,request.question)
        warnings.append('VERIFIED_EXTRACTIVE_FALLBACK')
    if candidate.provider_error:warnings.append(candidate.provider_error)
    selected=[e for e in evidence if e.evidence_id in candidate.evidence_ids]
    trusted=all(services.corpus.admits(e) for e in selected)
    post=evaluate(SafetyTask(stage='output',question=request.question,candidate=candidate.text,grounded=proof.verified and bool(selected),abstention=proof.verified and candidate.generation_mode=='clarification',evidence_ids=[e.evidence_id for e in selected],cited_ids=candidate.evidence_ids,trusted_evidence=trusted and proof.verified,prediction_present=prediction is not None,knowledge_available=bool(evidence),action=action))
    if not post.allowed:return {'status':'BLOCKED','response':safe_message(post),'evidence':[],'generation_mode':'withheld','safety':[pre,post],'prediction':prediction,'warnings':warnings,'retrieval_rounds':rounds,'grounding':proof}
    if post.decision!='ALLOW':warnings.extend(post.rule_ids)
    return {'status':'DEGRADED' if warnings or candidate.generation_mode!='llm' else 'COMPLETED','response':candidate.text,'evidence':selected,'generation_mode':candidate.generation_mode,'safety':[pre,post],'prediction':prediction,'warnings':warnings,'retrieval_rounds':rounds,'grounding':proof}
