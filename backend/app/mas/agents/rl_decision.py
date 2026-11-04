from dataclasses import replace
from backend.app.mas.agents.runtime import RLDecisionAgent as StubRL
from backend.app.schemas.contracts import AgentName,RLDecision
from backend.app.schemas.runtime import AgentResult,AgentStatus
from backend.app.rl.policy import PolicyService

class RLDecisionAgent(StubRL):
    def __init__(self,service=None):
        super().__init__();self.service=service if service is not None else PolicyService()
        self.definition=replace(self.definition,implementation='integrated',available=True,permitted_tools=('local_education_q_policy',),description='Selects educational interaction actions from trained synthetic-simulator Q policy, with explicit baseline fallback',timeout_seconds=3)
    async def execute(self,message):
        self.validate(message);task=message.payload
        band=0 if task.prediction is None else (1 if task.prediction.score<0.5 else 2)
        state=(band,('low','medium','high').index(task.simulated_knowledge_level),('low','medium','high').index(task.simulated_engagement_level),min(2,len(task.evidence)),int(task.safety_status=='restricted'),6,6)
        action,source,reason,version=self.service.choose(state)
        data={'prediction_band':('unavailable','lower-score','higher-score')[band],'simulated_knowledge_level':task.simulated_knowledge_level,'simulated_engagement_level':task.simulated_engagement_level,'evidence_availability':('none','partial','sufficient')[state[3]],'safety_status':task.safety_status,'encoder_state':list(state),'user_context_source':'SIMULATED_DEFAULTS_NOT_MEASURED','decision_reason':reason}
        return AgentResult(agent_id=AgentName.rl,status=AgentStatus.COMPLETED,implementation='integrated',output=RLDecision(state=data,action=action,policy_version=version,decision_source=source))
