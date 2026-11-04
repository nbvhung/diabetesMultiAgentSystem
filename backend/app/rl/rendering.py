"""Fixed educational interaction templates; no health claims or clinical actions."""
from backend.app.rl.mdp import ACTIONS
TEXT={
 ACTIONS[0]:'Model output is a research score, not a clinical diagnosis or a calibrated clinical probability.',
 ACTIONS[4]:'Please clarify which diabetes education topic or source you would like to review. No missing personal information is inferred.',
 ACTIONS[5]:'Consider discussing your questions and any model limitations with a qualified health professional. This system does not provide diagnosis or treatment.'}
QUESTION='Would you like to review what these source excerpts say in your own words?'

from dataclasses import dataclass

@dataclass(frozen=True)
class EducationPlan:
    text: str
    evidence_ids: list[str]
    proposed_action: str
    effective_action: str
    override_reason: str | None = None

def render_plan(action,evidence):
    if action not in ACTIONS:raise ValueError('Invalid educational action')
    if action in TEXT:return EducationPlan(TEXT[action],[],action,action)
    if not evidence:return EducationPlan(TEXT[ACTIONS[4]],[],action,ACTIONS[4],'NO_EVIDENCE_FOR_REQUESTED_ACTION')
    rendered='Retrieved NIDDK educational excerpts (not diagnosis or treatment instructions):\n'+'\n'.join(f'[{e.evidence_id}] {e.excerpt} (Source: {e.source_url}; section: {e.section})' for e in evidence)
    if action==ACTIONS[3]:rendered+='\n'+QUESTION
    return EducationPlan(rendered,[e.evidence_id for e in evidence],action,action)


def render_action(action,evidence):
    plan=render_plan(action,evidence)
    return plan.text,plan.evidence_ids
