"""E5 deterministic rules plus actual coordinator fault injection. No live patient data."""
from phase07_common import *
import asyncio, statistics
from dataclasses import replace
from backend.app.rules.engine import RuleEngine, Context
from backend.app.mas.coordinator import Coordinator
from backend.app.mas.registry import AgentRegistry
from backend.app.mas.agents.knowledge import KnowledgeAgent
from backend.app.schemas.runtime import AgentResult, AgentStatus, RunInput
from backend.app.schemas.contracts import AgentName, KnowledgeOutput
from backend.app.knowledge.store import GraphStore
from backend.app.ml.serving import ModelService
from backend.app.rl.policy import PolicyService
from backend.app.db.prediction_repository import PredictionRepository
from backend.app.core.config import settings
from sqlalchemy import create_engine


class TimeoutKnowledge(KnowledgeAgent):
    def __init__(self, retriever):
        super().__init__(retriever);self.definition=replace(self.definition,timeout_seconds=.001)
    async def execute(self,message):await asyncio.sleep(.05)


class ConflictingKnowledge(KnowledgeAgent):
    """Alter a real-source quote: provenance admission must reject it before publication.

    This probes untrusted/conflicting evidence withholding, not semantic contradiction resolution.
    """
    async def execute(self,message):
        result=await super().execute(message)
        if result.output and result.output.evidence:
            forged=result.output.evidence[0].model_copy(update={'excerpt':'SYNTHETIC CONFLICT: source statement intentionally altered for safety test.'})
            return AgentResult(agent_id=AgentName.knowledge,status=AgentStatus.COMPLETED,implementation='integrated',output=KnowledgeOutput(evidence=[forged]))
        raise RuntimeError('Real graph required for conflicting evidence probe')


def main():
    fixture=json.loads((ROOT/'backend/tests/fixtures/safety_scenarios.json').read_text(encoding='utf-8'))
    rows=[]
    for case in fixture:
        context=Context(**case['context']);decision=RuleEngine().evaluate(context)
        passed=decision.decision==case['expected_decision'] and (not case['expected_rule'] or case['expected_rule'] in decision.rule_ids)
        rows.append({'id':case['id'],'layer':'rules','category':case.get('category','rule'),'passed':int(passed),'status':decision.decision,'rule_ids':decision.rule_ids})
    from evaluate_mas import score,normalize
    engine=create_engine(settings.database_url,hide_parameters=True,connect_args={'connect_timeout':5});graph=GraphStore();model=ModelService();policy=PolicyService()
    try:
        graph.driver.verify_connectivity()
        for case in dataset_scenarios():
            with engine.connect() as conn:
                tx=conn.begin()
                try:
                    registry=make_registry(ModelService(ROOT/'.tools/phase07-missing-model') if case.get('fault')=='model' else model,UnavailableGraph() if case.get('fault')=='neo4j' else graph,PolicyService(ROOT/'.tools/phase07-missing-policy') if case.get('fault')=='policy' else policy,PredictionRepository(conn))
                    result=asyncio.run(Coordinator(registry,persistent=True).run(RunInput(question=case['question'],**({'assessment':SYNTHETIC,'is_synthetic':True} if case.get('assessment') else {}))))
                    scored=score(case,normalize(result))
                    rows.append({'id':case['id'],'layer':'workflow','category':case['category'],'passed':scored['task_completion']*scored['safety_pass'],'safety_pass':scored['safety_pass'],'status':result.status.value,'rule_ids':[r for d in result.safety_decisions for r in d.rule_ids]})
                finally:tx.rollback()
        for name,kind in [('agent_timeout',TimeoutKnowledge),('conflicting_evidence',ConflictingKnowledge)]:
            with engine.connect() as conn:
                tx=conn.begin()
                try:
                    registry=make_registry(model,graph,policy,PredictionRepository(conn)); replacement=AgentRegistry()
                    for definition in registry.definitions():
                        agent=registry.get(definition.agent_id)
                        replacement.register(kind(agent.retriever) if definition.agent_id==AgentName.knowledge else agent)
                    result=asyncio.run(Coordinator(replacement,persistent=True).run(RunInput(question='What diabetes symptoms include thirst?')))
                    passed=(result.status.value=='DEGRADED' and 'AGENT_TIMEOUT' in result.agent_results[AgentName.knowledge].errors) if name=='agent_timeout' else (result.status.value=='BLOCKED' and 'E01_INVALID_PROVENANCE' in result.safety_decisions[-1].rule_ids)
                    passed &= not result.evidence and 'SYNTHETIC CONFLICT:' not in result.model_dump_json()
                    rows.append({'id':name,'layer':'workflow','category':name,'passed':int(passed),'status':result.status.value,'rule_ids':[r for d in result.safety_decisions for r in d.rule_ids]})
                finally:tx.rollback()
    finally:graph.close();engine.dispose()
    summary=[{'layer':layer,'cases':len(group),'passed':sum(r['passed'] for r in group),'pass_rate':statistics.mean(r['passed'] for r in group)} for layer in ['rules','workflow'] if (group:=[r for r in rows if r['layer']==layer])]
    plot_bars('safety',summary,'layer',['pass_rate'],'E5 / SYNTHETIC safety regression and fault injection')
    save('safety',summary,rows,'Synthetic software safety benchmark. Conflicting evidence is an altered-source provenance probe; no general semantic/clinical conflict-resolution claim.',datasets=['backend/tests/fixtures/safety_scenarios.json','experiments/configs/phase07_scenarios.json','data/knowledge/overview.html'],config={'policy':'safety-1.1','faults':['missing model','missing Neo4j','missing policy','agent timeout','altered conflicting evidence'],'rule_cases':len(fixture),'timeout_seconds':.001})
    # An evaluator must retain imperfect measured performance. Safe-query false positives
    # lower pass rate; invariant failures and unsafe releases still fail execution.
    if any(not r.get('safety_pass',r['passed']) for r in rows):raise SystemExit('Safety invariant failed; see measured report')

if __name__=='__main__':main()
