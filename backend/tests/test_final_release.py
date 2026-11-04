import pytest
from backend.app.research.retrieval import query_topics,rewrite_query

@pytest.mark.parametrize('question,topic',[
    ('Những biểu hiện thường gặp của đái tháo đường?', 'symptoms'),
    ('Ai dễ mắc bệnh tiểu đường?', 'risk'),
    ('Làm sao trì hoãn tiểu đường týp 2?', 'prevention'),
    ('ABCs trong quản lý tiểu đường là gì?', 'management'),
    ('Hoạt động thể lực trong bệnh tiểu đường?', 'activity'),
])
def test_vietnamese_paraphrases_keep_specific_topic(question,topic):
    topics=query_topics(question)
    assert topic in topics
    assert rewrite_query(question,topics,retry=True)

def test_paraphrase_router_still_abstains_outside_domain():
    assert query_topics('Python biểu hiện lỗi gì?')==[]
    assert query_topics('Tell me about sugar')==[]
    assert query_topics('Biểu hiện của bệnh gút là gì?')==[]

def test_schema_retry_is_bounded_and_disclosed(monkeypatch):
    import asyncio
    from backend.app.research import grounding
    from backend.app.research.schemas import EducationOutput
    calls=[]
    async def rejected(*args):
        calls.append(args)
        return EducationOutput(text='SYNTHETIC FALLBACK',generation_mode='extractive',evidence_ids=[],llm_status='unavailable',provider_error='GROQ_STRUCTURED_OUTPUT_REJECTED')
    monkeypatch.setattr(grounding,'compose',rejected)
    output=asyncio.run(grounding.compose_with_schema_retry('SYNTHETIC','vi',[],None,None))
    assert len(calls)==2 and output.provider_error=='GROQ_SCHEMA_RETRY_EXHAUSTED'

def test_rate_limits_do_not_trigger_content_retry(monkeypatch):
    import asyncio
    from backend.app.research import grounding
    from backend.app.research.schemas import EducationOutput
    calls=[]
    async def limited(*args):
        calls.append(args)
        return EducationOutput(text='SYNTHETIC FALLBACK',generation_mode='extractive',evidence_ids=[],llm_status='unavailable',provider_error='GROQ_RATE_LIMITED')
    monkeypatch.setattr(grounding,'compose',limited)
    asyncio.run(grounding.compose_with_schema_retry('SYNTHETIC','vi',[],None,None))
    assert len(calls)==1
