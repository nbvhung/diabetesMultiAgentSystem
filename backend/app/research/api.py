"""Explicit v2 HTTP surface for runtime 3.0; historical v1 endpoints stay intact."""
from uuid import UUID
from fastapi import APIRouter,Request,HTTPException
from pydantic import ValidationError,BaseModel,Field
from typing import Literal
from threading import RLock
from backend.app.api.readiness import readiness as historical_readiness
from backend.app.schemas.contracts import AssessmentInput
from backend.app.schemas.runtime import AgentStatus
from backend.app.db.prediction_repository import LegacyRunRequiresReview
from .schemas import RunInput,WorkflowResponse,AgentId
from .corpus import Corpus
from .semantic import SemanticEncoder
from .graph import DiabetesGraph
from .retrieval import Retriever
from .llm import GroqService
from .agents import build_registry
from .coordinator import Coordinator
from .repository import ResearchRepository,get_run

router=APIRouter(prefix='/api/v2',tags=['diabetes-research-v2'])


class Services:
    def __init__(self,state,*,corpus=None,encoder=None,graph=None,llm=None):
        self.corpus=corpus or Corpus();self.encoder=encoder or SemanticEncoder()
        self.graph=graph or DiabetesGraph(state.knowledge_store);self.llm=llm or GroqService()
        self.retriever=Retriever(self.graph,self.corpus,self.encoder)
        self._warm=False;self._warm_lock=RLock();self.preparation_errors=[]
    def warmup(self):
        with self._warm_lock:
            if self._warm:return
            try:
                self.corpus.load();self.graph.summary()
                self.retriever.prepare();self.encoder.load();self.retriever.semantic_index();self.retriever.reranker.load()
            except Exception:
                # Availability is still checked by each real agent/probe. Never mark
                # a failed warmup as model/graph availability or synthesize vectors.
                self.preparation_errors=['RESEARCH_WARMUP_INCOMPLETE']
            self._warm=True


def services(request):
    state=request.app.state
    if not state.prediction_enabled:raise HTTPException(503,'RESEARCH_RUNTIME_REQUIRES_INTEGRATED_SERVICES')
    with state.research_lock:
        if state.research_services is None:state.research_services=Services(state)
    return state.research_services


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
    services(request)
    try:result=get_run(request.app.state.db_engine,run_id)
    except LegacyRunRequiresReview:raise HTTPException(409,'LEGACY_RUN_REQUIRES_REVIEW') from None
    except Exception:raise HTTPException(503,'PERSISTENCE_UNAVAILABLE') from None
    if result is None:raise HTTPException(404,'RUN_NOT_FOUND')
    return result


@router.get('/mas/runs/{run_id}/trace')
def trace(run_id:UUID,request:Request):
    result=read_run(run_id,request)
    return {'schema_version':result.schema_version,'run_id':result.run_id,'agent_trace':result.agent_trace}


@router.get('/mas/agents')
def agents(request:Request):
    svc=services(request);state=request.app.state
    registry=build_registry(state.model_service,None,state.policy_service,svc.retriever,svc.llm)
    return {'schema_version':'3.0','agents':[{'agent_id':s.agent_id,'description':s.description,'input_schema':s.input_schema.__name__,'output_schema':s.output_schema.__name__,'permitted_tools':s.permitted_tools,'timeout_seconds':s.timeout_seconds,'fallback_policy':s.fallback_policy} for s in registry.definitions()]}


@router.get('/system/readiness')
def readiness(request:Request):
    svc=services(request);result=historical_readiness(request)
    # Reuse infrastructure probes, but never relabel the historical v1 Safety
    # implementation as the policy actually used by this v2 workflow.
    try:
        from .safety import evaluate
        from .schemas import SafetyTask
        checked=evaluate(SafetyTask(stage='input',question='What is diabetes?'))
        result['components']['safety']={'status':'available','version':checked.policy_version,'schema_version':checked.schema_version,'scope':'mandatory deterministic input/output gates'}
    except Exception:
        result['components']['safety']={'status':'unavailable','code':'DIABETES_SAFETY_UNAVAILABLE'}
    for name,probe in [('diabetes_corpus',lambda:corpus_info(svc)),('diabetes_graph',lambda:svc.graph.summary()),('semantic_encoder',lambda:semantic_info(svc)),('reranker',lambda:reranker_info(svc))]:
        if name in ('semantic_encoder','reranker') and result['components'].get('diabetes_graph',{}).get('status')!='available':
            result['components'][name]={'status':'unverified','code':'NOT_PROBED_GRAPH_UNAVAILABLE'}
            continue
        try:result['components'][name]={'status':'available',**probe()}
        except Exception:result['components'][name]={'status':'unavailable','code':name.upper()+'_UNAVAILABLE'}
    result['components']['llm']=svc.llm.status()
    result['components']['evidence_verifier']={'status':'available','scope':'exact source checks; independent semantic review requires LLM'}
    result['runtime_version']='3.0';result['scope']='Diabetes research expansion; no clinical readiness claim'
    return result


def corpus_info(svc):
    svc.corpus.load()
    return {'version':svc.corpus.manifest['dataset_version'],'sources':svc.corpus.manifest['source_count'],'chunks':svc.corpus.manifest['chunk_count']}


def semantic_info(svc):
    svc.retriever.prepare();svc.encoder.load();svc.retriever.semantic_index()
    return {'version':svc.encoder.meta['model_id'],'source_revision':svc.encoder.meta['source_revision'],'device':'cpu','dimensions':384}


def reranker_info(svc):
    svc.retriever.reranker.load()
    return {'version':svc.retriever.reranker.meta['model_id'],'source_revision':svc.retriever.reranker.meta['source_revision'],'device':'cpu'}


@router.get('/knowledge/sources')
def sources(request:Request):
    svc=services(request)
    try:
        svc.corpus.load()
        return {'dataset_version':svc.corpus.manifest['dataset_version'],'sources':svc.corpus.manifest['sources'],'scope':'Registered diabetes education sources; timestamps are retrieval times, not clinical endorsement'}
    except Exception:raise HTTPException(503,'DIABETES_CORPUS_UNAVAILABLE') from None


@router.get('/knowledge/graph')
def graph(request:Request):
    svc=services(request)
    try:
        svc.corpus.load()
        assertions=svc.graph.store.read('MATCH (a:DiabetesAssertion {release:$release})-[:SUPPORTED_BY]->(c:DiabetesEvidence) RETURN a.subject AS subject,a.predicate AS predicate,a.object AS object,a.supporting_quote AS supporting_quote,a.extraction_rule AS extraction_rule,a.section_context AS section_context,c.id AS evidence_id,c.url AS source_url,c.text AS supporting_passage ORDER BY a.id LIMIT 100',release=svc.corpus.manifest['chunks_sha256'])
        return {**svc.graph.summary(),'assertions':assertions}
    except Exception:raise HTTPException(503,'DIABETES_GRAPH_UNAVAILABLE') from None


class SearchInput(BaseModel):
    question:str=Field(min_length=1,max_length=4000)
    strategy:Literal['lexical','semantic','graph','hybrid']='hybrid'
    k:int=Field(default=3,ge=1,le=5)


@router.post('/knowledge/search')
async def search(body:SearchInput,request:Request):
    import asyncio
    svc=services(request)
    try:return await asyncio.to_thread(svc.retriever.search,body.question,None,1,body.strategy,body.k)
    except Exception:raise HTTPException(503,'DIABETES_RETRIEVAL_UNAVAILABLE') from None
