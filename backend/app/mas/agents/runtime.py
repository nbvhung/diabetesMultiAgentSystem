"""No external tools or clinical inference are enabled in Phase 01."""
import re
import unicodedata
from backend.app.mas.agents.base import AgentDefinition
from backend.app.schemas.contracts import AgentName, EducationOutput, SafetyDecision
from backend.app.schemas.runtime import (AgentMessage, AgentResult, AgentStatus, INPUT_TYPES,
    OUTPUT_TYPES, EducationTask, SafetyTask)

def definition(name: AgentName, description: str, *, minimal: bool = False) -> AgentDefinition:
    return AgentDefinition(agent_id=name, description=description, input_schema=INPUT_TYPES[name],
        output_schema=OUTPUT_TYPES[name], implementation="minimal" if minimal else "stub",
        available=minimal, fallback_policy=("Fail closed; withhold content" if name == AgentName.safety
            else "Abstain without evidence; no fabricated clinical output"))

class RuntimeAgent:
    definition: AgentDefinition

    def validate(self, message: AgentMessage):
        if message.recipient != self.definition.agent_id or not isinstance(message.payload, self.definition.input_schema):
            raise ValueError("Agent recipient/input mismatch")

class UnavailableAgent(RuntimeAgent):
    def __init__(self, spec: AgentDefinition):
        self.definition = spec

    async def execute(self, message: AgentMessage) -> AgentResult:
        self.validate(message)
        return AgentResult(agent_id=self.definition.agent_id, status=AgentStatus.UNAVAILABLE,
            implementation="stub", errors=["TOOL_NOT_INTEGRATED"])

class PredictionAgent(UnavailableAgent):
    def __init__(self):
        super().__init__(definition(AgentName.prediction, "Calls versioned DL inference; model not integrated"))

class KnowledgeAgent(UnavailableAgent):
    def __init__(self):
        super().__init__(definition(AgentName.knowledge, "Retrieves attributable Neo4j/RAG evidence; tool not integrated"))

class RLDecisionAgent(UnavailableAgent):
    def __init__(self):
        super().__init__(definition(AgentName.rl, "Selects educational action using a compatible policy; none integrated"))

ABSTENTION = ("Chưa có nguồn tri thức được truy hồi để trả lời câu hỏi giáo dục có dẫn chứng. "
    "Hệ thống không tạo dự đoán nguy cơ hoặc trích dẫn thay thế cho công cụ chưa tích hợp. "
    "Bạn có thể chuẩn bị câu hỏi để trao đổi với nhân viên y tế. Đây không phải chẩn đoán hay chỉ dẫn điều trị.")
REFUSAL = ("Hệ thống không cung cấp hướng dẫn về liều thuốc hoặc tự điều chỉnh điều trị. "
    "Hãy trao đổi trực tiếp với nhân viên y tế phụ trách. Nội dung chưa được phát hành vì giới hạn an toàn.")
FAIL_CLOSED = "Không thể xác minh an toàn của câu trả lời. Nội dung được giữ lại; vui lòng trao đổi với nhân viên y tế."

class EducationAgent(RuntimeAgent):
    definition = definition(AgentName.education, "Produces a transparent abstention; no clinical synthesis without retrieval", minimal=True)

    async def execute(self, message: AgentMessage) -> AgentResult:
        self.validate(message)
        task: EducationTask = message.payload
        # No clinical template or generated claim: only disclose tool limitations.
        text = ABSTENTION
        if task.prediction is None:
            text += " Không có kết quả mô hình để diễn giải."
        return AgentResult(agent_id=AgentName.education, status=AgentStatus.COMPLETED,
            implementation="minimal", output=EducationOutput(text=text, evidence_ids=[]))

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold()).replace("đ", "d")
    return "".join(c for c in text if not unicodedata.combining(c))

def safety_rules(question: str, candidate: str) -> list[str]:
    query, output = normalize(question), normalize(candidate)
    rules = []
    # Conservative intent gate. This is a bounded lexical rule set, not a clinical engine.
    if re.search(r"\b(lieu|dosage|dose|dosing|tang|giam|ngung|increase|decrease|stop|bao nhieu|how much|how many)\b", query) and re.search(
        r"\b(thuoc|insulin|metformin|medication|medicine|drug|tablet|vien|units)\b", query):
        rules.append("S01_MEDICATION_DOSING")
    if re.search(r"\b(chac chan|chan doan xac dinh|definitely|certainly)\b", output):
        rules.append("S02_DIAGNOSTIC_CERTAINTY")
    if re.search(r"\b\d+(?:[.,]\d+)?\s*(mg|mcg|ml|units|don vi|vien)\b", output):
        rules.append("S03_OUTPUT_DOSAGE")
    return rules

class LegacySafetyAgent(RuntimeAgent):
    definition = definition(AgentName.safety, "Minimal deterministic output and medication-intent safety gate", minimal=True)

    async def execute(self, message: AgentMessage) -> AgentResult:
        self.validate(message)
        task: SafetyTask = message.payload
        rules = safety_rules(task.question or "", task.candidate)
        return AgentResult(agent_id=AgentName.safety, status=AgentStatus.COMPLETED,
            implementation="minimal", output=SafetyDecision(allowed=not rules,
                severity="warning" if rules else "info", rule_ids=rules,
                reason="Content withheld by minimal safety rules" if rules else "Passed bounded Phase 01 checks; not clinical validation"))

# Current public agent; legacy minimal policy retained only as historical code.
from backend.app.mas.agents.safety import SafetyAgent
