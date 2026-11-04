from typing import Literal
from pydantic import model_validator
from backend.app.schemas.contracts import EducationOutput as EducationV1

class EducationOutput(EducationV1):
    schema_version: Literal['1.1'] = '1.1'
    proposed_action: str | None = None
    effective_action: str | None = None
    override_reason: str | None = None


    @model_validator(mode='after')
    def validate_plan(self):
        from backend.app.rl.mdp import ACTIONS
        if any(a is not None and a not in ACTIONS for a in (self.proposed_action,self.effective_action)):
            raise ValueError('Invalid education action metadata')
        if (self.proposed_action is None)!=(self.effective_action is None):raise ValueError('Incomplete education plan')
        if self.proposed_action!=self.effective_action and not self.override_reason:raise ValueError('Override requires reason')
        return self
