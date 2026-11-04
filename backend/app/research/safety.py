"""Versioned research safety 2.0; historical safety-1.1 remains unchanged."""
from dataclasses import replace
import re
from backend.app.rules.engine import RuleEngine,Context,RULES,norm
from .schemas import SafetyDecision


def categorical_diagnosis(context):
    if context.stage!='output':return False
    text=norm(context.candidate)
    # Conditional public education is not a categorical personal diagnosis. Retain
    # the explicit certainty checks, and don't waive the rule merely for a citation.
    return bool(re.search(r'(?<!if )(?<!when )you (?:definitely |certainly )?(?:have|do not have|dont have) (?:type [12] )?(?:diabetes|prediabetes)|you are (?:not )?(?:diabetic|prediabetic)|(?<!neu )ban (?:chac chan )?(?:mac|khong mac|bi|khong bi) (?:benh )?tieu duong|chac chan|chan doan xac dinh|definitely|certainly',text))


CURRENT_RULES=tuple(replace(rule,condition=categorical_diagnosis,version='diabetes-safety-2.0') if rule.rule_id=='S02_DIAGNOSTIC_CERTAINTY' else rule for rule in RULES)


def evaluate(task):
    data={key:value for key,value in task.model_dump().items() if key in Context.__dataclass_fields__}
    data['question']=task.question or ''
    result=RuleEngine(CURRENT_RULES).evaluate(Context(**data))
    return SafetyDecision(**result.model_dump(exclude={'schema_version','timestamp','policy_version'}))


REFUSAL='Hệ thống không cung cấp chẩn đoán cá nhân, kê đơn hoặc thay đổi liều thuốc. Hãy trao đổi với nhân viên y tế phụ trách về quyết định điều trị.'
FAIL_CLOSED='Chưa xác minh được an toàn hoặc bằng chứng của câu trả lời. Nội dung được giữ lại; vui lòng trao đổi với nhân viên y tế.'


def safe_message(decision):
    if 'SYS01_SAFETY_FAILURE' in decision.rule_ids:return FAIL_CLOSED
    if decision.decision=='ESCALATE':return 'Tình huống được mô tả có thể cần hỗ trợ y tế khẩn cấp. Hãy liên hệ dịch vụ cấp cứu địa phương hoặc tìm trợ giúp y tế ngay.'
    if decision.decision=='REQUEST_CLARIFICATION':return 'Vui lòng làm rõ câu hỏi giáo dục về diabetes. Hệ thống không suy diễn thông tin cá nhân hoặc dữ liệu còn thiếu.'
    return REFUSAL
