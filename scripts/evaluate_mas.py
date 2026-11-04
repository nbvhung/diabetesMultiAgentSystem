"""E3: paired genuine MAS vs strong monolithic workflow, same tools, no superiority assumption."""
from phase07_common import *
import asyncio, random, statistics, time
from sqlalchemy import create_engine
from backend.app.core.config import settings
from backend.app.ml.serving import ModelService
from backend.app.rl.policy import PolicyService
from backend.app.knowledge.store import GraphStore
from backend.app.mas.coordinator import Coordinator
from backend.app.db.prediction_repository import PredictionRepository
from backend.app.schemas.runtime import RunInput
from backend.app.schemas.contracts import AgentName
from phase07_baseline import run_single


def normalize(run):
    return {'run_id':str(run.run_id),'status':run.status.value,'response':run.response,'evidence':run.evidence,'prediction':run.agent_results[AgentName.prediction].output,'decision':run.agent_results[AgentName.rl].output.model_dump() if run.agent_results[AgentName.rl].output else None,'safety':run.safety_decisions,'errors':[error for result in run.agent_results.values() for error in result.errors],'warnings':run.warnings}


def score(case, result):
    evidence=result['evidence']; rules={r for d in result['safety'] for r in d.rule_ids}
    successful=result['status']==case['expected_status']
    successful &= bool(evidence)==case['evidence']
    if 'prediction' in case:successful &= (result['prediction'] is not None)==case['prediction']
    if case.get('sections'): successful &= bool({e.section for e in evidence}&set(case['sections']))
    if case.get('rule'):successful &= case['rule'] in rules
    if case.get('agent_error'):successful &= case['agent_error'] in result['errors']
    if case.get('policy_source'):successful &= result['decision'] is not None and result['decision']['decision_source']==case['policy_source']
    provenance=admitted(evidence) if evidence else None
    correctness=(sum(e.section in case.get('sections',[]) and admitted([e]) for e in evidence)/len(evidence)) if evidence else None
    safety_ok=len(result['safety'])==2 and [d.stage for d in result['safety']]==['input','output']
    safety_ok &= all(d.allowed for d in result['safety']) if result['status'] not in ('BLOCKED','FAILED') else not evidence
    if case.get('rule'):safety_ok &= case['rule'] in rules
    return {'task_completion':int(successful),'evidence_correctness':correctness,'citation_provenance':int(provenance) if provenance is not None else None,'evidence_count':len(evidence),'safety_pass':int(safety_ok)}


def main():
    engine=create_engine(settings.database_url,hide_parameters=True,connect_args={'connect_timeout':5})
    model=ModelService();model.load();policy=PolicyService();policy.load();graph=GraphStore();graph.driver.verify_connectivity()
    cases=dataset_scenarios(); rows=[]; rng=random.Random(SEED)
    try:
        # Shared warmup before timing, preventing the first method paying model/policy load.
        from backend.app.rag.retrieval import Retrieval
        Retrieval(graph).search('diabetes symptoms')
        tasks=[(repeat,case) for repeat in range(3) for case in cases];rng.shuffle(tasks)
        for repeat,case in tasks:
            services=(ModelService(ROOT/'.tools/phase07-missing-model') if case.get('fault')=='model' else model,
                      UnavailableGraph() if case.get('fault')=='neo4j' else graph,
                      PolicyService(ROOT/'.tools/phase07-missing-policy') if case.get('fault')=='policy' else policy)
            request=RunInput(question=case['question'],**({'assessment':SYNTHETIC,'is_synthetic':True} if case.get('assessment') else {}))
            methods=['single_workflow','multi_agent'];rng.shuffle(methods)
            for method in methods:
                # Identical actual prediction writes, transaction rollback and setup exclusion.
                # No benchmark baseline snapshot is misrepresented as a production MAS run.
                with engine.connect() as connection:
                    tx=connection.begin()
                    try:
                        repository=PredictionRepository(connection)
                        started=time.perf_counter()
                        if method=='multi_agent':
                            registry=make_registry(*services,repository)
                            result=normalize(asyncio.run(Coordinator(registry,persistent=True).run(request)))
                        else: result=run_single(request,*services,repository)
                        elapsed=(time.perf_counter()-started)*1000
                        rows.append({'method':method,'scenario':case['id'],'category':case['category'],'repeat':repeat,'status':result['status'],'latency_ms':elapsed,**score(case,result),
                                     'prediction_score':result['prediction'].score if result['prediction'] else None,
                                     'retrieved_ids':[e.evidence_id for e in result['evidence']],
                                     'rl_action':result['decision']['action'] if result['decision'] else None,
                                     'response_sha256':__import__('hashlib').sha256(result['response'].encode()).hexdigest()})
                    finally:tx.rollback()
    finally:graph.close();engine.dispose()
    summary=[]
    for method in ['single_workflow','multi_agent']:
        group=[r for r in rows if r['method']==method]; ev=[r for r in group if r['evidence_correctness'] is not None]
        summary.append({'method':method,'tasks':len(group),'task_completion':statistics.mean(r['task_completion'] for r in group),'evidence_correctness':statistics.mean(r['evidence_correctness'] for r in ev) if ev else None,'citation_provenance':statistics.mean(r['citation_provenance'] for r in ev) if ev else None,'evidence_cases':len(ev),'safety_pass_rate':statistics.mean(r['safety_pass'] for r in group),'latency_ms':statistics.mean(r['latency_ms'] for r in group),'latency_p95_ms':float(__import__('numpy').percentile([r['latency_ms'] for r in group],95))})
    plot_bars('mas',summary,'method',['task_completion','safety_pass_rate','latency_ms'],'E3 / same-tool paired workflows; local software benchmark')
    pairs={(r['scenario'],r['repeat']):{} for r in rows}
    for row in rows:pairs[(row['scenario'],row['repeat'])][row['method']]=row
    fields=['status','prediction_score','retrieved_ids','rl_action','response_sha256']
    mismatches=[{'scenario':scenario,'repeat':repeat,'fields':[field for field in fields if pair['single_workflow'][field]!=pair['multi_agent'][field]]} for (scenario,repeat),pair in pairs.items() if any(pair['single_workflow'][field]!=pair['multi_agent'][field] for field in fields)]
    save('mas',summary,rows,'12 SYNTHETIC project-authored scenarios × 3 repeats per method. No claim of clinical benefit or statistically established MAS superiority.',datasets=['experiments/configs/phase07_scenarios.json','data/knowledge/overview.html','artifacts/models/pima-mlp-0.2.0/manifest.json','artifacts/policies/education-q-1.1/manifest.json'],config={'repeats':3,'ordering':'seeded shuffled scenarios and paired method order','access':'same frozen model/preprocessing, Neo4j hybrid corpus, serving RL policy, render_plan and RuleEngine gates','single_workflow':'direct service calls, no agent registry/messages/coordinator','latency_scope':'workflow computation incl prediction INSERT; connection/reflection, rollback and snapshot serialization excluded equally; warm model/policy/corpus','evidence_correctness':'fraction of returned evidence with exact admitted provenance AND relevant ground-truth section, averaged across evidence-bearing cases; empty cases excluded','citation_provenance':'exact admitted source metadata/excerpt/URL, independent of topical relevance','completion':'expected status + expected prediction/evidence presence + relevant section + expected rule/error/fallback','inference':'descriptive comparison; no significance claim'},extra={'paired_output_mismatches':mismatches})

if __name__=='__main__':main()
