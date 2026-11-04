from dataclasses import replace
from backend.app.mas.agents.runtime import PredictionAgent as StubPrediction
from backend.app.schemas.runtime import AgentResult,AgentStatus
from backend.app.schemas.contracts import AgentName
from backend.app.schemas.prediction import PredictionResult
from backend.app.ml.serving import ModelUnavailable

class PredictionAgent(StubPrediction):
    def __init__(self,service,repository=None):
        super().__init__(); self.service=service; self.repository=repository
        self.definition=replace(self.definition,implementation='integrated',available=True,
            output_schema=PredictionResult,permitted_tools=('pytorch_inference','postgres_prediction_write'),timeout_seconds=30,
            fallback_policy='UNAVAILABLE for invalid/missing artifacts; persistence errors fail the transaction, never return unstored success')

    async def execute(self,message):
        self.validate(message)
        try: result=self.service.predict(message.payload.assessment)
        except ModelUnavailable:
            return AgentResult(agent_id=AgentName.prediction,status=AgentStatus.UNAVAILABLE,implementation='integrated',errors=['MODEL_UNAVAILABLE'])
        if self.repository is None: raise RuntimeError('PERSISTENCE_REQUIRED')
        result=self.repository.persist_prediction(message.run_id,message.payload.assessment,result,self.service)
        return AgentResult(agent_id=AgentName.prediction,status=AgentStatus.COMPLETED,implementation='integrated',output=result)
