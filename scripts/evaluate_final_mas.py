"""Actual MAS vs same-tool fixed workflow, paired on public-source synthetic questions."""
from phase07_common import *
import asyncio,random,statistics,time
from types import SimpleNamespace
from sqlalchemy import create_engine
from backend.app.core.config import settings
from backend.app.ml.serving import ModelService
from backend.app.rl.policy import PolicyService
from backend.app.knowledge.store import GraphStore
from backend.app.research.api import Services
from backend.app.research.config import ResearchSettings
from backend.app.research.llm import GroqService
from backend.app.research.schemas import RunInput,AgentId
from backend.app.research.agents import build_registry
from backend.app.research.coordinator import Coordinator
from backend.app.research.repository import ResearchRepository
from final_baseline import run_single
from evaluate_diabetes_rag import questions


def normalize(run):
    return {'status':run.status.value,'response':run.response,'evidence':run.evidence,'generation_mode':run.generation_mode,'safety':run.safety_decisions,'prediction':run.agent_results[AgentId.prediction].output,'warnings':run.warnings,'retrieval_rounds':run.retrieval_rounds,'grounding':run.grounding}


def main():
    state=SimpleNamespace(model_service=ModelService(),policy_service=PolicyService(),knowledge_store=GraphStore())
    # Offline coordination benchmark is explicit: do not spend hundreds of remote calls
    # or pretend extracts are generated answers. Live LLM validation has a separate CLI.
    svc=Services(state,llm=GroqService(ResearchSettings(groq_api_key=None)))
    svc.warmup();state.model_service.load();state.policy_service.load()
    cases=[r for r in questions(svc.corpus) if r['split']=='diagnostic_phrasing']
    cases=cases[:12]+[r for r in questions(svc.corpus) if not r['relevant_ids']]
    config=json.loads((ROOT/'experiments/configs/diabetes_benchmark.json').read_text(encoding='utf-8'))
    cases.extend({'id':r['id'],'question':r['question'],'relevant_ids':[],'required_rule':r['rule'],'language':'en','split':'adversarial'} for r in config['adversarial'])
    engine=create_engine(settings.database_url,hide_parameters=True,connect_args={'connect_timeout':5});rows=[];rng=random.Random(SEED)
    pairs=[(repeat,case) for repeat in range(2) for case in cases];rng.shuffle(pairs)
    try:
        for repeat,case in pairs:
            request=RunInput(question=case['question'],language='vi' if case['language']=='vi' else 'en')
            methods=['single_workflow','multi_agent'];rng.shuffle(methods)
            for method in methods:
                with engine.connect() as connection:
                    tx=connection.begin()
                    try:
                        repo=ResearchRepository(connection);started=time.perf_counter()
                        if method=='multi_agent':result=normalize(asyncio.run(Coordinator(build_registry(state.model_service,repo,state.policy_service,svc.retriever,svc.llm),svc.corpus).run(request)))
                        else:result=asyncio.run(run_single(request,state,svc,repo))
                        elapsed=(time.perf_counter()-started)*1000;evidence=result['evidence'];ids=[e.evidence_id for e in evidence]
                        rules={r for d in result['safety'] for r in d.rule_ids};relevant=set(case['relevant_ids'])
                        success=(bool(set(ids)&relevant) and result['status'] in ('COMPLETED','DEGRADED')) if relevant else (not evidence and (case.get('required_rule') in rules if case.get('required_rule') else True))
                        invariant=len(result['safety'])==2 and (all(d.allowed for d in result['safety']) if result['status'] not in ('BLOCKED','FAILED') else not evidence)
                        rows.append({'method':method,'question_id':case['id'],'repeat':repeat,'status':result['status'],'generation_mode':result['generation_mode'],'educational_evidence_task_completed':int(success),'evidence_relevance':sum(i in relevant for i in ids)/len(ids) if ids and relevant else None,'citation_provenance':int(all(svc.corpus.admits(e) for e in evidence)) if evidence else None,'safety_invariant':int(invariant),'retrieval_rounds':result['retrieval_rounds'],'latency_ms':elapsed,'llm_generated':int(result['generation_mode']=='llm')})
                    finally:tx.rollback()
    finally:state.knowledge_store.close();engine.dispose()
    summary=[]
    for method in ['single_workflow','multi_agent']:
        group=[r for r in rows if r['method']==method];evidence=[r for r in group if r['evidence_relevance'] is not None]
        summary.append({'method':method,'runs':len(group),'task_completion':statistics.mean(r['educational_evidence_task_completed'] for r in group),'evidence_relevance':statistics.mean(r['evidence_relevance'] for r in evidence) if evidence else None,'citation_provenance':statistics.mean(r['citation_provenance'] for r in evidence) if evidence else None,'safety_invariants':statistics.mean(r['safety_invariant'] for r in group),'latency_ms':statistics.mean(r['latency_ms'] for r in group),'llm_generated_runs':sum(r['llm_generated'] for r in group)})
    plot_bars('final_mas',summary,'method',['task_completion','safety_invariants','latency_ms'],'Same-tool diabetes workflows / actual extractive fallback benchmark; LLM disabled')
    save('final_mas',summary,rows,'Real orchestration, actual Neo4j + semantic retrieval; LLM explicitly disabled in both methods. This is not an evaluation of generated LLM answer quality.',datasets=['experiments/configs/diabetes_benchmark.json','data/knowledge/diabetes-v2/manifest.json'],config={'seed':SEED,'repeats':2,'access':'same corpus, retriever, policy, compose/verify functions and deterministic safety; baseline calls them directly','llm_mode':'explicitly disabled in both to isolate offline workflow behavior; live test separate','timing':'workflow computation only; SQL connection/reflection/rollback excluded equally','task_completion':'correct evidence availability/relevant passage or expected refusal; not clinical/LLM correctness','comparison':'matched maximum caps: two retrieval rounds, two drafts, four provider attempts each; provider disabled; same 22 cases twice; offline control, not clinical or live-LLM quality; latency descriptive'})

if __name__=='__main__':main()
