"""Bounded Groq structured inference. No training, arbitrary URLs, tools or raw logs."""
from datetime import datetime,timezone
from dataclasses import dataclass
import json,re
import httpx
from pydantic import BaseModel,ValidationError
from .config import research_settings


class LLMUnavailable(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def redact_question(text):
    text=re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b','[EMAIL_REDACTED]',text)
    text=re.sub(r'(?<!\w)(?:\+?\d[\d ()-]{8,}\d)(?!\w)','[PHONE_OR_ID_REDACTED]',text)
    return text[:3000]


@dataclass(frozen=True)
class Completion:
    parsed:BaseModel
    model:str
    input_tokens:int
    output_tokens:int


class GroqService:
    ENDPOINT='https://api.groq.com/openai/v1/chat/completions'
    def __init__(self,config=None,transport=None):
        self.config=config or research_settings;self.transport=transport;self.last_success=None
    @property
    def configured(self):return bool(self.config.diabetes_llm_enabled and self.config.groq_api_key and self.config.groq_api_key.get_secret_value() and not self.config.groq_api_key.get_secret_value().startswith('REPLACE_'))
    def status(self):
        return {'status':'available' if self.last_success else 'configured_unverified' if self.configured else 'unavailable','provider':'Groq','model':self.config.groq_model,'last_verified_at':self.last_success,'code':None if self.last_success else 'LLM_DISABLED_BY_CONFIGURATION' if not self.config.diabetes_llm_enabled else 'LLM_NOT_VERIFIED' if self.configured else 'GROQ_API_KEY_NOT_CONFIGURED'}
    async def complete(self,*,purpose,system,data,schema):
        if not self.configured:raise LLMUnavailable('LLM_DISABLED_BY_CONFIGURATION' if not self.config.diabetes_llm_enabled else 'GROQ_API_KEY_NOT_CONFIGURED')
        body={'model':self.config.groq_model,'temperature':0,'max_completion_tokens':self.config.groq_max_output_tokens,
              'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(data,ensure_ascii=False)}],
              'response_format':{'type':'json_schema','json_schema':{'name':purpose,'strict':True,'schema':schema.model_json_schema()}}}
        if self.config.groq_model.startswith('openai/gpt-oss-'):
            # Groq exposes GPT-OSS reasoning separately. Keep it out of structured
            # publication and reserve the bounded completion budget for the JSON.
            body.update(reasoning_effort='low',include_reasoning=False)
        if len(json.dumps(body,ensure_ascii=False))>35000:raise LLMUnavailable('LLM_CONTEXT_BUDGET_EXCEEDED')
        # No automatic content-retry: a failed or truncated clinical/education response is
        # not partially released. Coordinator chooses an explicit grounded fallback.
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.config.groq_timeout_seconds,connect=5),follow_redirects=False,transport=self.transport) as client:
                response=await client.post(self.ENDPOINT,json=body,headers={'Authorization':'Bearer '+self.config.groq_api_key.get_secret_value()})
            if response.status_code==429:raise LLMUnavailable('GROQ_RATE_LIMITED')
            if response.status_code in (401,403):raise LLMUnavailable('GROQ_AUTHENTICATION_FAILED')
            if response.status_code>=400:
                try:code=response.json().get('error',{}).get('code')
                except (ValueError,AttributeError,TypeError):code=None
                if code=='json_validate_failed':raise LLMUnavailable('GROQ_STRUCTURED_OUTPUT_REJECTED')
                raise LLMUnavailable('GROQ_REQUEST_FAILED')
            payload=response.json();choice=payload['choices'][0]
            if choice.get('finish_reason')!='stop':raise LLMUnavailable('LLM_INCOMPLETE_RESPONSE')
            content=choice['message'].get('content')
            if not isinstance(content,str) or len(content)>18000:raise LLMUnavailable('LLM_INVALID_RESPONSE')
            parsed=schema.model_validate_json(content)
            usage=payload.get('usage',{})
            incoming=usage.get('prompt_tokens',0);outgoing=usage.get('completion_tokens',0)
            if type(incoming)!=int or type(outgoing)!=int or min(incoming,outgoing)<0:raise LLMUnavailable('LLM_INVALID_USAGE')
            model=payload.get('model')
            if model!=self.config.groq_model:raise LLMUnavailable('LLM_MODEL_ID_MISMATCH')
            self.last_success=datetime.now(timezone.utc).isoformat()
            return Completion(parsed,model,incoming,outgoing)
        except LLMUnavailable:raise
        except httpx.TimeoutException:raise LLMUnavailable('GROQ_TIMEOUT') from None
        except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError,ValidationError):raise LLMUnavailable('LLM_UNAVAILABLE_OR_INVALID') from None
