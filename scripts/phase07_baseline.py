"""E3 monolithic reference: same tools/evidence/templates/policy and two safety gates.

No Coordinator, AgentRegistry, message dispatch or Agent execution. This is deliberately
a strong fixed sequential workflow, not an evidence-deprived straw-man baseline.
"""
from uuid import uuid4
from phase07_common import admitted
from backend.app.rules.engine import Context, RuleEngine
from backend.app.mas.coordinator import Coordinator
from backend.app.ml.serving import ModelUnavailable
from backend.app.knowledge.store import KnowledgeUnavailable
from backend.app.rag.retrieval import Retrieval
from backend.app.rl.rendering import render_plan
from backend.app.rl.mdp import ACTIONS


def run_single(request, model, graph, policy, repository):
    run_id=uuid4(); engine=RuleEngine(); warnings=[]; errors=[]
    pre=engine.evaluate(Context(question=request.question or '', assessment=request.assessment.model_dump() if request.assessment else None))
    if not pre.allowed:
        text=Coordinator.safe_message(pre)
        post=engine.evaluate(Context(stage='output',question=request.question or '',candidate=text,abstention=True))
        return dict(run_id=str(run_id),status='BLOCKED',response=text,evidence=[],prediction=None,decision=None,safety=[pre,post],errors=errors,warnings=warnings)
    prediction=None; evidence=[]
    if request.assessment:
        try:
            prediction=model.predict(request.assessment)
            prediction=repository.persist_prediction(run_id,request.assessment,prediction,model)
            warnings.extend(prediction.warnings)
        except ModelUnavailable: errors.append('MODEL_UNAVAILABLE')
    knowledge_available=False
    if request.question:
        try: evidence=Retrieval(graph).search(request.question); knowledge_available=True
        except KnowledgeUnavailable: errors.append('NEO4J_UNAVAILABLE')
        if not evidence and knowledge_available:warnings.append('NO_EVIDENCE')
    band=0 if prediction is None else (1 if prediction.score<.5 else 2)
    state=(band,1,1,min(2,len(evidence)),int(pre.decision!='ALLOW'),6,6)
    action,source,reason,version=policy.choose(state)
    if source=='fallback':warnings.append('RL_POLICY_FALLBACK:'+reason)
    if action not in ACTIONS:raise ValueError('Policy returned non-whitelisted action')
    plan=render_plan(action,evidence)
    post=engine.evaluate(Context(stage='output',question=request.question or '',candidate=plan.text,evidence_ids=[e.evidence_id for e in evidence],cited_ids=plan.evidence_ids,trusted_evidence=admitted(evidence),grounded=bool(evidence) and bool(plan.evidence_ids),abstention=not plan.evidence_ids,prediction_present=prediction is not None,knowledge_available=knowledge_available,action=action))
    warnings.extend(r for d in [pre,post] if d.decision!='ALLOW' for r in d.rule_ids)
    return dict(run_id=str(run_id),status='BLOCKED' if not post.allowed else 'DEGRADED' if warnings or errors else 'COMPLETED',response=plan.text if post.allowed else Coordinator.safe_message(post),evidence=evidence if post.allowed else [],prediction=prediction,decision={'action':action if post.allowed else 'WITHHELD_BY_SAFETY','decision_source':source,'policy_version':version},safety=[pre,post],errors=errors,warnings=warnings)
