from datetime import datetime, timezone
from typing import Literal
from pydantic import Field, AwareDatetime, model_validator
from backend.app.schemas.contracts import SafetyDecision as SafetyV1

Decision = Literal['ALLOW','ALLOW_WITH_WARNING','BLOCK','ESCALATE','REQUEST_CLARIFICATION']
class SafetyDecision(SafetyV1):
    schema_version: Literal['1.1'] = '1.1'
    decision: Decision
    checked_content: str
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: Literal['safety-1.1'] = 'safety-1.1'
    stage: Literal['input','output']

    @model_validator(mode='after')
    def consistent(self):
        if self.allowed != (self.decision in ('ALLOW','ALLOW_WITH_WARNING')):
            raise ValueError('Decision/allowed mismatch')
        if not self.rule_ids: raise ValueError('Every safety decision requires rule IDs')
        return self
