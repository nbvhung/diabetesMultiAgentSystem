from backend.app.mas.agents.base import AgentDefinition
from backend.app.schemas.contracts import AgentName
from backend.app.schemas.runtime import SafetyTask,AgentResult,AgentStatus
from backend.app.schemas.safety import SafetyDecision
from backend.app.rules.engine import Context,RuleEngine

class SafetyAgent:
    definition=AgentDefinition(agent_id=AgentName.safety,description='Versioned deterministic input/output safety policy with veto authority',input_schema=SafetyTask,output_schema=SafetyDecision,implementation='integrated',available=True,timeout_seconds=2,fallback_policy='Fail closed: no business actions without preflight, no candidate release without output gate')
    def __init__(self,engine=None):self.engine=engine if engine is not None else RuleEngine()
    async def execute(self,message):
        if message.recipient!=AgentName.safety or not isinstance(message.payload,SafetyTask):raise ValueError('Invalid safety task')
        task=message.payload
        context=Context(stage=task.stage,question=task.question or '',candidate=task.candidate,assessment=task.assessment,evidence_ids=tuple(task.evidence_ids),cited_ids=tuple(task.cited_ids),trusted_evidence=task.trusted_evidence,grounded=task.grounded,abstention=task.abstention,prediction_present=task.prediction_present,knowledge_available=task.knowledge_available,action=task.action)
        return AgentResult(agent_id=AgentName.safety,status=AgentStatus.COMPLETED,implementation='integrated',output=self.engine.evaluate(context))
