"""Deterministic versioned policy; not a clinical triage or diagnosis model."""
from dataclasses import dataclass,field
import re,unicodedata
from typing import Callable
from pydantic import ValidationError
from backend.app.schemas.contracts import AssessmentInput
from backend.app.schemas.safety import SafetyDecision

VERSION='safety-1.1'
from backend.app.rl.mdp import ACTIONS
def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold().replace('đ','d')) if not unicodedata.combining(c))
def match(pattern,text): return bool(re.search(pattern,norm(text)))

@dataclass(frozen=True)
class Context:
    stage: str='input'
    question: str=''
    candidate: str=''
    assessment: dict | None=None
    evidence_ids: tuple[str,...]=()
    cited_ids: tuple[str,...]=()
    trusted_evidence: bool=True
    grounded: bool=False
    abstention: bool=False
    prediction_present: bool=False
    knowledge_available: bool=True
    action: str=''

@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: str
    description: str
    condition: Callable[[Context],bool]
    priority: int
    action: str
    severity: str
    version: str=VERSION

def invalid_assessment(c):
    if c.stage!='input' or c.assessment is None: return False
    try: AssessmentInput.model_validate(c.assessment,strict=True);return False
    except ValidationError: return True

def dose(text):
    return match(r'\b(lieu|dose|dosage|dosing|tang|giam|ngung|increase|decrease|stop|bao nhieu|how much|how many|double)\b',text) and match(r'\b(thuoc|insulin|metformin|medication|medicine|drug|tablet|vien|units)\b',text)

def emergency(c):
    if c.stage!='input':return False
    # Conservative lexical referral, never a diagnosis. Pure educational definitions
    # without a personal/current emergency description stay educational.
    q=norm(c.question)
    danger=bool(re.search(r'khong tho|kho tho|bat tinh|co giat|unconscious|seizure|cannot breathe|can.t breathe|trouble breathing|chest pain|dau nguc',q))
    personal=bool(re.search(r"i (am|have|can't|cannot)|i'm|my (father|mother|child|dad)|toi|bo toi|me toi|con toi|someone|right now|help|cap cuu",q))
    educational=bool(re.search(r'what (is|are)|explain|definition|la gi|tim hieu',q))
    return danger and (personal or not educational)

RULES=(
 Rule('R01_EMERGENCY','escalation','Described immediate serious situation: stop automated advice',emergency,1000,'ESCALATE','critical'),
 Rule('I01_INVALID_ASSESSMENT','input','Reject invalid/incomplete assessment; never infer missing features',invalid_assessment,950,'REQUEST_CLARIFICATION','warning'),
 Rule('I02_MISSING_DATA','input','Personal prediction requires assessment',lambda c:c.stage=='input' and (not c.question.strip() and c.assessment is None or c.assessment is None and match(r'predict my|assess my|my risk|nguy co cua toi',c.question)),940,'REQUEST_CLARIFICATION','warning'),
 Rule('W01_PROMPT_INJECTION','workflow','Do not obey attempts to bypass policy',lambda c:match(r'ignore.{0,35}(rules|instructions|safety)|bypass.{0,20}safety|bo qua.{0,20}(luat|quy tac)|system prompt|developer:',c.question+' '+c.candidate),930,'BLOCK','warning'),
 Rule('S01_MEDICATION_DOSING','input','Do not adjust individual medication doses',lambda c:dose(c.question),920,'BLOCK','warning'),
 Rule('I03_PRESCRIPTION','input','Do not prescribe medicines',lambda c:match(r'prescribe|ke don|which (drug|medication) should i|what (drug|medicine) should i',c.question),910,'BLOCK','warning'),
 Rule('I04_DIAGNOSIS_REQUEST','input','Do not diagnose or rule out disease',lambda c:match(r'do i have diabetes|am i diabetic|diagnose me|toi co bi tieu duong|chan doan cho toi|tell me i (have|do not have)',c.question),900,'BLOCK','warning'),
 Rule('W04_ACTION_NOT_ALLOWED','workflow','Only the six educational RL actions are permitted',lambda c:c.stage=='output' and bool(c.action) and c.action not in ACTIONS,895,'BLOCK','warning'),
 Rule('W02_UNSAFE_ACTION','workflow','RL/tool action cannot override safety',lambda c:c.stage=='output' and match(r'insulin|dose|prescribe|diagnos|ke don|lieu thuoc',c.action),890,'BLOCK','warning'),
 Rule('S02_DIAGNOSTIC_CERTAINTY','output','No categorical disease claim',lambda c:c.stage=='output' and match(r'you (definitely |certainly )?(have|do not have|dont have) diabetes|you are (not )?diabetic|ban (chac chan )?(mac|khong mac|bi|khong bi) (benh )?tieu duong|chac chan|chan doan xac dinh|definitely|certainly',c.candidate),880,'BLOCK','warning'),
 Rule('S03_OUTPUT_DOSAGE','output','No dosing instructions in output',lambda c:c.stage=='output' and not c.abstention and (dose(c.candidate) or match(r'\b[0-9]+(?:[.,][0-9]+)?\s*(mg|mcg|ml|units|don vi|vien)\b',c.candidate)),870,'BLOCK','warning'),
 Rule('O02_TEST_SUBSTITUTION','output','Prediction cannot replace diagnostic tests',lambda c:c.stage=='output' and match(r'replace.{0,30}(test|xet nghiem)|no need.{0,20}(test|blood)|khong can.{0,20}xet nghiem',c.candidate),860,'BLOCK','warning'),
 Rule('E01_INVALID_PROVENANCE','evidence','Do not release unverified or invented citations',lambda c:c.stage=='output' and (not c.trusted_evidence or not set(c.cited_ids)<=set(c.evidence_ids)),850,'BLOCK','warning'),
 Rule('E02_UNGROUNDED_OUTPUT','evidence','Only admitted excerpts or explicit abstention may be released',lambda c:c.stage=='output' and not(c.grounded or c.abstention),840,'BLOCK','warning'),
 Rule('I05_OUT_OF_SCOPE','input','Known nonmedical domains need clarification',lambda c:c.stage=='input' and match(r'python|bicycle|stock price|football|weather|crypto',c.question),500,'REQUEST_CLARIFICATION','info'),
 Rule('E03_NO_EVIDENCE','evidence','Disclose unavailable or empty knowledge',lambda c:c.stage=='output' and (not c.evidence_ids or not c.knowledge_available),200,'ALLOW_WITH_WARNING','warning'),
 Rule('W03_RESEARCH_SCORE','workflow','Prediction is uncertain research output, not a diagnosis',lambda c:c.stage=='output' and c.prediction_present,190,'ALLOW_WITH_WARNING','warning'),
)

class RuleEngine:
    def __init__(self,rules=RULES):
        self.rules=tuple(sorted(rules,key=lambda r:(-r.priority,r.rule_id)))
        if len({r.rule_id for r in self.rules})!=len(self.rules): raise ValueError('Duplicate rule id')
        if not self.rules:raise ValueError('Empty safety policy')
    def evaluate(self,c:Context):
        if c.stage not in ('input','output'):raise ValueError('Unknown safety stage')
        hits=[r for r in self.rules if r.condition(c)]
        decision=hits[0].action if hits else 'ALLOW'
        return SafetyDecision(allowed=decision in ('ALLOW','ALLOW_WITH_WARNING'),decision=decision,
            severity=hits[0].severity if hits else 'info',rule_ids=[r.rule_id for r in hits] or ['P00_ALLOW'],
            reason='; '.join(r.description for r in hits) if hits else 'No configured safety condition matched',
            checked_content=f'stage={c.stage}; question_chars={len(c.question)}; candidate_chars={len(c.candidate)}; assessment_present={c.assessment is not None}; evidence_count={len(c.evidence_ids)}',stage=c.stage)
