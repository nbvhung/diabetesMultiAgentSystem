from typing import Protocol
import re,time,unicodedata
import numpy as np
from backend.app.knowledge.store import TOPICS,embedding,validate_url,safe_text
from backend.app.schemas.contracts import EvidenceItem

def keywords(question):
 q=''.join(c for c in unicodedata.normalize('NFKD',question.lower().replace('đ','d')) if not unicodedata.combining(c))
 return list(dict.fromkeys(entity for _,entity,aliases in TOPICS.values() if any(re.search(r'(?<!\w)'+re.escape(a)+r'(?!\w)',q) for a in aliases)))

class Retriever(Protocol):
 def search(self,question:str,k:int=5): ...

class Retrieval:
 def __init__(self,store,strategy='hybrid'):
  if strategy not in ('vector','graph','hybrid'): raise ValueError('Unknown strategy')
  self.store=store;self.strategy=strategy
 def search(self,question,k=5):
  if not 1<=k<=10: raise ValueError('k must be 1..10')
  entities=keywords(question)
  if not entities: return []
  # Expand only controlled bilingual entity aliases, never execute user-generated Cypher.
  vector=np.asarray(embedding(question+' '+' '.join(entities)))
  merged={}
  modes=['vector','graph'] if self.strategy=='hybrid' else [self.strategy]
  for mode in modes:
   rows=self.store.candidates(None if mode=='vector' else entities)
   ranking=[]
   for row in rows:
    c=row['c']
    if not safe_text(c['text']): continue
    validate_url(c['url'])
    cosine=float(np.dot(vector,np.asarray(c['embedding'])))
    if mode=='vector' and cosine<0.08: continue
    ranking.append((cosine,c))
   ranking.sort(key=lambda x:(-x[0],x[1]['id']))
   for rank,(_,c) in enumerate(ranking[:20],1):
    old=merged.get(c['id'],(0,c)); merged[c['id']]=(old[0]+1/(60+rank),c)
  ordered=sorted(merged.values(),key=lambda x:(-x[0],x[1]['id']))[:k]
  return [EvidenceItem(evidence_id=c['id'],source_title=c['title'],source_url=c['url'],publisher=c['publisher'],section=c['section'],retrieved_at=c['retrieved_at'],excerpt=c['text']) for _,c in ordered]
