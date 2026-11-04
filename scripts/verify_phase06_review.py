"""Replay the original review failures without modifying policy or clinical data."""
from pathlib import Path
import sys,json,asyncio,re
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.rl.policy import PolicyService
from backend.app.rl.experiments import evaluate,TEST_SEEDS
from backend.app.rl.mdp import ACTIONS
from backend.app.mas.registry import AgentRegistry
from backend.app.mas.coordinator import Coordinator
from backend.app.mas.agents.runtime import PredictionAgent,KnowledgeAgent,RLDecisionAgent as StubRL
from backend.app.mas.agents.knowledge import EducationAgent
from backend.app.mas.agents.safety import SafetyAgent
from backend.app.schemas.runtime import AgentResult,AgentStatus,RunInput
from backend.app.schemas.contracts import AgentName,RLDecision
ROOT=Path(__file__).resolve().parents[1];LOG=ROOT/'docs/validation/phase06_fixes'
failures=[]
for bad in ['START_METFORMIN','ADJUST_MEDICATION','TAKE_5_MG_METFORMIN','UNSUPPORTED_ACTION','']:
 class FaultyRL(StubRL):
  def __init__(self):
   super().__init__();self.definition=replace(self.definition,implementation='integrated',available=True)
  async def execute(self,message):
   return AgentResult(agent_id=AgentName.rl,status=AgentStatus.COMPLETED,implementation='integrated',output=RLDecision(state={'label':'SYNTHETIC_REVIEW_PROBE'},action=bad,policy_version='SYNTHETIC_REVIEW_ONLY',decision_source='policy'))
 registry=AgentRegistry()
 for agent in [PredictionAgent(),KnowledgeAgent(),FaultyRL(),EducationAgent(),SafetyAgent()]:registry.register(agent)
 run=asyncio.run(Coordinator(registry).run(RunInput(question='What is diabetes?')))
 assert run.status.value=='BLOCKED' and run.agent_results[AgentName.education].status==AgentStatus.SKIPPED
 assert run.agent_results[AgentName.rl].output is None
 assert 'W04_ACTION_NOT_ALLOWED' in run.safety_decisions[-1].rule_ids
 assert not bad or bad not in run.model_dump_json()
 failures.append({'synthetic_invalid_action':bad,'workflow_status':run.status.value,'raw_action_returned':False,'safety_rule_ids':run.safety_decisions[-1].rule_ids})
service=PolicyService();service.load()
deployed=evaluate(service.q,TEST_SEEDS,decision_fn=service.choose)
shared=evaluate(service.q,TEST_SEEDS,visits=service.visits)
assert deployed==shared and shared['fallback_decisions']>0
import nbformat
nb=nbformat.read(ROOT/'notebooks/04_rl_q_learning_training.ipynb',as_version=4)
stream=''.join(o.get('text','') for c in nb.cells if c.cell_type=='code' for o in c.get('outputs',[]) if o.output_type=='stream')
printed=[int(x) for x in re.findall(r'"selected_seed":\s*(\d+)',stream)]
assert printed and all(x==service.manifest.selected_seed for x in printed)
api=json.loads((LOG/'api_workflows.json').read_text())
plans=[]
for case in api:
 out=case['run']['agent_results']['education']['output']
 if out and 'proposed_action' in out:
  plans.append({'case':case['case'],'proposed_action':out['proposed_action'],'effective_action':out['effective_action'],'override_reason':out['override_reason']})
assert any(x['proposed_action']!=x['effective_action'] and x['override_reason'] for x in plans)
text=(ROOT/'frontend/src/main.tsx').read_text(encoding='utf-8')
assert 'PHASE 06' in text and 'PHASE 01' not in text and 'chưa tích hợp mô hình' not in text
report={'H1':{'status':'PASS','probes':failures},'H2':{'status':'PASS','policy_version':service.manifest.policy_version,'compared_episodes':len(TEST_SEEDS),'mismatches':0,'fallback_decisions':shared['fallback_decisions'],'reward':shared['average_episode_reward'],'completion_rate':shared['completion_rate']},'M1':{'status':'PASS','education_plans':plans},'L1':{'status':'PASS','manifest_seed':service.manifest.selected_seed,'printed_seeds':printed},'L2':{'status':'PASS','scope':'source text verified plus independent frontend build; no browser claim'}}
(LOG/'review_probes.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print({key:value['status'] for key,value in report.items()})
