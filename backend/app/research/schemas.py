"""Runtime 3.0 contracts; v1/v2.4 historical contracts are not relabeled."""
from datetime import datetime,timezone
from enum import Enum
from typing import Annotated,Literal
from uuid import UUID,uuid4
from pydantic import BaseModel,ConfigDict,Field,AwareDatetime,model_validator
from backend.app.schemas.contracts import AssessmentInput,RLDecision
from backend.app.schemas.prediction import PredictionResult
from backend.app.schemas.runtime import AgentStatus,WorkflowStatus


class Strict(BaseModel):model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Contract(Strict):schema_version:Literal['3.0']='3.0'
class AgentId(str,Enum):
    prediction='prediction';knowledge='knowledge';rl='rl';education='education';verifier='verifier';safety='safety'


class RunInput(Contract):
    question:str|None=Field(default=None,min_length=1,max_length=4000)
    assessment:AssessmentInput|None=None
    is_synthetic:Literal[True]|None=None
    language:Literal['vi','en']='vi'
    @model_validator(mode='after')
    def check(self):
        if self.question is not None:
            self.question=self.question.strip()
            if not self.question:raise ValueError('Empty question')
        if self.question is None and self.assessment is None:raise ValueError('Question or assessment required')
        if self.assessment is not None and not self.is_synthetic:raise ValueError('Synthetic confirmation required')
        return self


class Evidence(Contract):
    evidence_id:str=Field(pattern='^[a-f0-9]{64}$')
    source_id:str
    source_title:str
    source_url:str
    publisher:Literal['NIDDK']='NIDDK'
    section:str
    section_context:str|None=None
    excerpt:str=Field(min_length=45,max_length=1000)
    retrieved_at:AwareDatetime
    source_version:str=Field(pattern='^[a-f0-9]{64}$')
    topics:list[str]
    retrieval_score:float=Field(ge=0,le=1)
    last_reviewed:str|None=None
    @model_validator(mode='after')
    def url(self):
        from .corpus import validate_source_url
        validate_source_url(self.source_url)
        return self


# LLM JSON schemas intentionally have no defaults: every property must be required
# under Groq strict structured output. They are untrusted until independently checked.
class Support(Strict):
    evidence_id:str
    quote:str=Field(min_length=15,max_length=1000)
class Claim(Strict):
    claim_id:str=Field(pattern='^c[1-4]$')
    text:str=Field(min_length=8,max_length=700)
    supports:list[Support]=Field(min_length=1,max_length=3)
class Draft(Strict):
    claims:list[Claim]=Field(max_length=4)
    insufficient_evidence:bool
    @model_validator(mode='after')
    def consistent(self):
        ids=[c.claim_id for c in self.claims]
        if len(ids)!=len(set(ids)) or self.insufficient_evidence==bool(self.claims):raise ValueError('Inconsistent claims/abstention')
        return self


class Entailment(Strict):
    claim_id:str
    supported:bool
    contradicted:bool
    reason:Literal['SUPPORTED','NOT_SUPPORTED','CONTRADICTED','INSUFFICIENT_CONTEXT']
class Review(Strict):verdicts:list[Entailment]=Field(min_length=1,max_length=4)


class PredictionTask(Contract):assessment:AssessmentInput
class KnowledgeTask(Contract):
    question:str
    query:str
    attempt:int=Field(ge=1,le=2)
class RLTask(Contract):
    prediction:PredictionResult|None=None
    evidence:list[Evidence]=Field(default_factory=list)
class EducationTask(Contract):
    question:str|None
    language:Literal['vi','en']
    evidence:list[Evidence]
    decision:RLDecision|None=None
    feedback:list[str]=Field(default_factory=list)
class KnowledgeOutput(Contract):
    evidence:list[Evidence]
    query_topics:list[str]
    coverage:float=Field(ge=0,le=1)
    adequate:bool
    semantic_available:bool
    retrieval_method:str
    attempt:int
    reranker_available:bool=False
class EducationOutput(Contract):
    text:str
    evidence_ids:list[str]
    claims:list[Claim]=Field(default_factory=list)
    generation_mode:Literal['llm','extractive','clarification','withheld']
    llm_status:Literal['available','unavailable','not_called']
    llm_model:str|None=None
    provider_error:str|None=None
    input_tokens:int=Field(default=0,ge=0)
    output_tokens:int=Field(default=0,ge=0)
    proposed_action:str|None=None
    effective_action:str|None=None
    override_reason:str|None=None
    @model_validator(mode='after')
    def check(self):
        if self.generation_mode=='llm' and (not self.claims or self.llm_status!='available' or not self.llm_model):raise ValueError('LLM mode requires genuine response metadata/claims')
        if self.generation_mode!='llm' and self.claims:raise ValueError('Only LLM mode contains translated claims')
        from backend.app.rl.mdp import ACTIONS
        if any(a is not None and a not in ACTIONS for a in (self.proposed_action,self.effective_action)):raise ValueError('Invalid educational action')
        if self.proposed_action!=self.effective_action and not self.override_reason:raise ValueError('Policy override requires reason')
        return self
class VerifierTask(Contract):
    candidate:EducationOutput
    evidence:list[Evidence]
    question:str|None=None
class VerifierOutput(Contract):
    verified:bool
    mode:Literal['exact_quote','independent_llm','abstention','rejected']
    candidate_sha256:str
    checked_claims:int
    reason_codes:list[str]
    input_tokens:int=0
    output_tokens:int=0
class SafetyTask(Contract):
    stage:Literal['input','output']
    question:str|None=None
    candidate:str=''
    assessment:dict|None=None
    grounded:bool=False
    abstention:bool=False
    evidence_ids:list[str]=Field(default_factory=list)
    cited_ids:list[str]=Field(default_factory=list)
    trusted_evidence:bool=True
    prediction_present:bool=False
    knowledge_available:bool=True
    action:str=''
class SafetyDecision(Contract):
    allowed:bool
    decision:Literal['ALLOW','ALLOW_WITH_WARNING','BLOCK','ESCALATE','REQUEST_CLARIFICATION']
    severity:str
    rule_ids:list[str]
    reason:str
    checked_content:str
    stage:Literal['input','output']
    policy_version:Literal['diabetes-safety-2.0']='diabetes-safety-2.0'
    @model_validator(mode='after')
    def check(self):
        if not self.rule_ids or self.allowed!=(self.decision in ('ALLOW','ALLOW_WITH_WARNING')):raise ValueError('Inconsistent safety decision')
        return self


INPUT_TYPES={AgentId.prediction:PredictionTask,AgentId.knowledge:KnowledgeTask,AgentId.rl:RLTask,AgentId.education:EducationTask,AgentId.verifier:VerifierTask,AgentId.safety:SafetyTask}
OUTPUT_TYPES={AgentId.prediction:PredictionResult,AgentId.knowledge:KnowledgeOutput,AgentId.rl:RLDecision,AgentId.education:EducationOutput,AgentId.verifier:VerifierOutput,AgentId.safety:SafetyDecision}


class Message(Contract):
    message_id:UUID=Field(default_factory=uuid4)
    run_id:UUID
    recipient:AgentId
    sender:Literal['coordinator']='coordinator'
    payload:PredictionTask|KnowledgeTask|RLTask|EducationTask|VerifierTask|SafetyTask
    @model_validator(mode='after')
    def check(self):
        if not isinstance(self.payload,INPUT_TYPES[self.recipient]):raise ValueError('Agent payload mismatch')
        return self
class Result(Contract):
    agent_id:AgentId
    status:AgentStatus
    implementation:Literal['integrated']='integrated'
    output:PredictionResult|KnowledgeOutput|RLDecision|EducationOutput|VerifierOutput|SafetyDecision|None=None
    errors:list[str]=Field(default_factory=list)
    @model_validator(mode='after')
    def check(self):
        if self.status==AgentStatus.COMPLETED:
            if self.errors or not isinstance(self.output,OUTPUT_TYPES[self.agent_id]):raise ValueError('Completed output mismatch')
        elif self.output is not None:raise ValueError('Non-completed output forbidden')
        return self
class Event(Contract):
    sequence:int=Field(ge=1)
    run_id:UUID
    message_id:UUID|None=None
    agent_id:AgentId|None=None
    status:AgentStatus|WorkflowStatus
    reason:str
    attempt:int=1
    duration_ms:float|None=Field(default=None,ge=0)
    input_summary:dict=Field(default_factory=dict)
    output_summary:dict=Field(default_factory=dict)
    rule_ids:list[str]=Field(default_factory=list)
    safety_decision:str|None=None
    safety_stage:str|None=None
    action:str|None=None
    policy_version:str|None=None
    decision_source:str|None=None
    timestamp:AwareDatetime=Field(default_factory=lambda:datetime.now(timezone.utc))
class WorkflowResponse(Contract):
    run_id:UUID
    status:WorkflowStatus
    response:str
    evidence:list[Evidence]
    agent_results:dict[AgentId,Result]
    agent_trace:list[Event]
    safety_decisions:list[SafetyDecision]
    warnings:list[str]
    limitations:list[str]
    generation_mode:Literal['llm','extractive','clarification','withheld']
    grounding:VerifierOutput|None=None
    retrieval_rounds:int=Field(ge=0,le=2)
    corpus_version:str|None=None
    @model_validator(mode='after')
    def audit(self):
        if self.status not in (WorkflowStatus.COMPLETED,WorkflowStatus.DEGRADED,WorkflowStatus.BLOCKED,WorkflowStatus.FAILED):raise ValueError('Terminal response required')
        if set(self.agent_results)!=set(AgentId):raise ValueError('All agent statuses required')
        if [d.stage for d in self.safety_decisions]!=['input','output']:raise ValueError('Both ordered safety gates required')
        if any(not d.allowed for d in self.safety_decisions) and self.status not in (WorkflowStatus.BLOCKED,WorkflowStatus.FAILED):raise ValueError('Veto cannot release')
        if [e.sequence for e in self.agent_trace]!=list(range(1,len(self.agent_trace)+1)) or any(e.run_id!=self.run_id for e in self.agent_trace):raise ValueError('Trace correlation mismatch')
        if self.generation_mode in ('llm','extractive','clarification') and self.status in (WorkflowStatus.COMPLETED,WorkflowStatus.DEGRADED):
            from .grounding import candidate_digest,render_claims,render_extractive,CLARIFICATION
            candidate=self.agent_results[AgentId.education].output
            if not isinstance(candidate,EducationOutput) or not self.grounding or not self.grounding.verified or self.grounding.candidate_sha256!=candidate_digest(candidate):raise ValueError('Released output requires matching verifier proof')
            if self.response!=candidate.text or set(candidate.evidence_ids)!={e.evidence_id for e in self.evidence}:raise ValueError('Released candidate/citations mismatch')
            expected=render_claims(candidate.claims) if self.generation_mode=='llm' else render_extractive(self.evidence) if self.generation_mode=='extractive' else candidate.text
            if candidate.text!=expected or (self.generation_mode=='clarification' and (candidate.text not in CLARIFICATION.values() or candidate.claims or candidate.evidence_ids)):raise ValueError('Unverified surrounding prose forbidden')
            verifier=self.agent_results[AgentId.verifier]
            if verifier.status!=AgentStatus.COMPLETED or verifier.output!=self.grounding:raise ValueError('Verifier audit mismatch')
            if self.generation_mode=='llm' and self.grounding.mode!='independent_llm':raise ValueError('LLM response requires independent semantic review')
        from backend.app.rl.mdp import ACTIONS
        rl=self.agent_results[AgentId.rl]
        if rl.output and rl.output.action not in ACTIONS and not (self.status in (WorkflowStatus.BLOCKED,WorkflowStatus.FAILED) and rl.output.action=='WITHHELD_BY_SAFETY'):raise ValueError('Invalid RL action')
        if self.status in (WorkflowStatus.BLOCKED,WorkflowStatus.FAILED) and self.evidence:raise ValueError('Veto withholds evidence')
        return self
