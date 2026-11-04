from dataclasses import replace
from backend.app.mas.agents.runtime import KnowledgeAgent as StubKnowledge,EducationAgent as StubEducation,ABSTENTION
from backend.app.schemas.contracts import AgentName,KnowledgeOutput,EducationOutput
from backend.app.schemas.education import EducationOutput
from backend.app.schemas.runtime import AgentResult,AgentStatus
from backend.app.knowledge.store import KnowledgeUnavailable,safe_text,validate_url

class KnowledgeAgent(StubKnowledge):
 def __init__(self,retriever):
  super().__init__();self.retriever=retriever
  self.definition=replace(self.definition,implementation='integrated',available=True,permitted_tools=('neo4j_read','hybrid_retrieval'),timeout_seconds=15,description='Retrieves evidence from curated NIDDK Neo4j corpus')
 async def execute(self,message):
  self.validate(message)
  try: evidence=self.retriever.search(message.payload.question)
  except KnowledgeUnavailable:
   return AgentResult(agent_id=AgentName.knowledge,status=AgentStatus.UNAVAILABLE,implementation='integrated',errors=['NEO4J_UNAVAILABLE'])
  # Empty successful search is distinct from infrastructure failure.
  return AgentResult(agent_id=AgentName.knowledge,status=AgentStatus.COMPLETED,implementation='integrated',output=KnowledgeOutput(evidence=evidence))

class EducationAgent(StubEducation):
 definition=replace(StubEducation.definition,description='Deterministic source-excerpt response with explicit citations; no LLM',implementation='integrated',output_schema=EducationOutput)
 async def execute(self,message):
  self.validate(message)
  evidence=[]
  for item in message.payload.evidence:
   if not safe_text(item.excerpt): continue
   try: validate_url(str(item.source_url))
   except ValueError: continue
   evidence.append(item)
  from backend.app.rl.rendering import render_plan
  from backend.app.rl.mdp import ACTIONS
  decision=message.payload.decision
  if decision is not None and decision.action in ACTIONS:
   plan=render_plan(decision.action,evidence)
   return AgentResult(agent_id=AgentName.education,status=AgentStatus.COMPLETED,implementation='integrated',output=EducationOutput(text=plan.text,evidence_ids=plan.evidence_ids,proposed_action=plan.proposed_action,effective_action=plan.effective_action,override_reason=plan.override_reason))
  elif not evidence:
   text=ABSTENTION; ids=[]
  else:
   # Documents remain quoted data; never interpreted as instructions or free-form claims.
   text='Retrieved NIDDK educational excerpts (not diagnosis or treatment instructions):\n'+'\n'.join(f'[{e.evidence_id}] {e.excerpt} (Source: {e.source_url}; section: {e.section})' for e in evidence)
   ids=[e.evidence_id for e in evidence]
  return AgentResult(agent_id=AgentName.education,status=AgentStatus.COMPLETED,implementation='integrated',output=EducationOutput(text=text,evidence_ids=ids))
