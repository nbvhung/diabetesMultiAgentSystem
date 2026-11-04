"""Six bounded agents with distinct contracts/tool rights and request-local execution."""
from dataclasses import dataclass
import asyncio,math
from uuid import UUID
from backend.app.schemas.contracts import AgentName,EvidenceItem
from backend.app.schemas.runtime import AgentMessage as OldMessage,PredictionTask as OldPredictionTask,RLTask as OldRLTask
from backend.app.mas.agents.prediction import PredictionAgent as ServingPredictionAgent
from backend.app.mas.agents.rl_decision import RLDecisionAgent
from backend.app.rl.mdp import ACTIONS
from backend.app.knowledge.store import KnowledgeUnavailable
from .schemas import *
from .llm import GroqService,LLMUnavailable
from .grounding import compose,verify_candidate
from . import safety


@dataclass(frozen=True)
class Definition:
    agent_id:AgentId
    description:str
    input_schema:type
    output_schema:type
    permitted_tools:tuple[str,...]
    timeout_seconds:float
    fallback_policy:str


class Agent:
    def __init__(self,name,description,tools,timeout,fallback):
        self.definition=Definition(name,description,INPUT_TYPES[name],OUTPUT_TYPES[name],tools,timeout,fallback)
    def check(self,message):
        if message.recipient!=self.definition.agent_id or not isinstance(message.payload,self.definition.input_schema):raise ValueError('Task contract mismatch')
    def completed(self,output):return Result(agent_id=self.definition.agent_id,status=AgentStatus.COMPLETED,output=output)
    def unavailable(self,code):return Result(agent_id=self.definition.agent_id,status=AgentStatus.UNAVAILABLE,errors=[code])


class PredictionAgent(Agent):
    def __init__(self,model,repository):
        super().__init__(AgentId.prediction,'Frozen research MLP on synthetic features',('pytorch_inference','postgres_prediction_write'),30,'Missing artifact -> unavailable; no alternate model')
        self.delegate=ServingPredictionAgent(model,repository)
    async def execute(self,message):
        self.check(message)
        old=await self.delegate.execute(OldMessage(run_id=message.run_id,recipient=AgentName.prediction,payload=OldPredictionTask(assessment=message.payload.assessment)))
        return Result(agent_id=AgentId.prediction,status=old.status,output=old.output,errors=old.errors)


class KnowledgeAgent(Agent):
    def __init__(self,retriever):
        super().__init__(AgentId.knowledge,'Diabetes domain routing, Neo4j evidence retrieval and multilingual reranking',('diabetes_neo4j_read','local_multilingual_embedding','source_snapshot_read'),20,'No graph/corpus -> unavailable; weak evidence -> ask Coordinator to retrieve again')
        self.retriever=retriever
    async def execute(self,message):
        self.check(message);task=message.payload
        try:output=await asyncio.to_thread(self.retriever.search,task.question,task.query,task.attempt)
        except KnowledgeUnavailable:return self.unavailable('NEO4J_UNAVAILABLE')
        except (OSError,ValueError,KeyError):return self.unavailable('DIABETES_CORPUS_UNAVAILABLE')
        return self.completed(output)


class PolicyAgent(Agent):
    def __init__(self,policy):
        super().__init__(AgentId.rl,'Existing simulator-trained educational policy; no clinical actions',('local_education_q_policy',),3,'Explicit named rule fallback')
        self.delegate=RLDecisionAgent(policy)
    async def execute(self,message):
        self.check(message);task=message.payload
        evidence=[EvidenceItem(evidence_id=e.evidence_id,source_title=e.source_title,source_url=e.source_url,publisher=e.publisher,section=e.section,excerpt=e.excerpt,retrieved_at=e.retrieved_at) for e in task.evidence]
        result=await self.delegate.execute(OldMessage(run_id=message.run_id,recipient=AgentName.rl,payload=OldRLTask(prediction=task.prediction,evidence=evidence)))
        if result.output and result.output.action not in ACTIONS:return Result(agent_id=AgentId.rl,status=AgentStatus.FAILED,errors=['RL_ACTION_NOT_ALLOWED'])
        return Result(agent_id=AgentId.rl,status=result.status,output=result.output,errors=result.errors)


class EducationAgent(Agent):
    def __init__(self,llm):
        super().__init__(AgentId.education,'Bounded diabetes source-grounded composition; explicitly labeled extractive fallback',('groq_structured_diabetes_composition',),30,'LLM missing/failed -> exact admitted source quotes, never simulated LLM prose')
        self.llm=llm
    async def execute(self,message):
        self.check(message);task=message.payload
        return self.completed(await compose(task.question,task.language,task.evidence,task.decision,self.llm,task.feedback))


class VerifierAgent(Agent):
    def __init__(self,corpus,llm):
        super().__init__(AgentId.verifier,'Source admission, exact quote/number checks, independent claim support review',('source_snapshot_read','groq_independent_entailment_review'),30,'Unsupported claim or unavailable semantic review -> reject; never approve by author self-report')
        self.corpus=corpus;self.llm=llm
    async def execute(self,message):
        self.check(message);task=message.payload
        return self.completed(await verify_candidate(task.candidate,task.evidence,self.corpus,self.llm,task.question))


class SafetyAgent(Agent):
    def __init__(self):super().__init__(AgentId.safety,'Mandatory input/output deterministic veto, independent of LLM',('diabetes_safety_rules_2',),2,'Fail closed')
    async def execute(self,message):self.check(message);return self.completed(safety.evaluate(message.payload))


class Registry:
    def __init__(self):self.agents={}
    def register(self,agent):
        spec=agent.definition
        if spec.agent_id in self.agents or not math.isfinite(spec.timeout_seconds) or spec.timeout_seconds<=0:raise ValueError('Invalid/duplicate agent definition')
        self.agents[spec.agent_id]=agent
    def get(self,name):return self.agents.get(name)
    def definitions(self):return tuple(a.definition for a in self.agents.values())


class RunLLMBudget:
    """Per-run usage, no cross-user conversation state or unbounded repair loop."""
    def __init__(self,provider):self.provider=provider;self.calls=0
    async def complete(self,**kwargs):
        if self.calls>=4:raise LLMUnavailable('LLM_CALL_BUDGET_EXCEEDED')
        self.calls+=1
        return await self.provider.complete(**kwargs)


def build_registry(model,repository,policy,retriever,llm):
    registry=Registry();budget=RunLLMBudget(llm)
    for agent in (PredictionAgent(model,repository),KnowledgeAgent(retriever),PolicyAgent(policy),EducationAgent(budget),VerifierAgent(retriever.corpus,budget),SafetyAgent()):registry.register(agent)
    return registry
