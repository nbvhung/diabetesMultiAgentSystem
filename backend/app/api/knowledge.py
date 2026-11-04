from fastapi import APIRouter,Request,HTTPException
from pydantic import BaseModel,Field
from typing import Literal
from backend.app.rag.retrieval import Retrieval
from backend.app.knowledge.store import KnowledgeUnavailable
router=APIRouter(prefix='/api/v1/knowledge',tags=['knowledge-debug'])
class SearchInput(BaseModel):
    question:str=Field(min_length=1,max_length=4000)
    strategy:Literal['vector','graph','hybrid']='hybrid'
    k:int=Field(default=5,ge=1,le=10)
@router.get('/health')
@router.get('/graph/summary')
def summary(request:Request):
    try: return request.app.state.knowledge_store.summary()
    except (KnowledgeUnavailable,AttributeError): raise HTTPException(503,'NEO4J_UNAVAILABLE') from None
@router.post('/search')
def search(body:SearchInput,request:Request):
    try:
        evidence=Retrieval(request.app.state.knowledge_store,body.strategy).search(body.question,body.k)
        return {'outcome':'FOUND' if evidence else 'NO_EVIDENCE','evidence':evidence}
    except (KnowledgeUnavailable,AttributeError): raise HTTPException(503,'NEO4J_UNAVAILABLE') from None
