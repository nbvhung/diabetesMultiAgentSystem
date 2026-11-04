"""Bounded, deterministic NIDDK corpus. No user Cypher or LLM extraction."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse
from urllib.request import urlopen
import hashlib,json,re,os
import numpy as np
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import HashingVectorizer
from neo4j import GraphDatabase,READ_ACCESS
from backend.app.schemas.contracts import EvidenceItem
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'data/knowledge'
URL='https://www.niddk.nih.gov/health-information/diabetes/overview'
COPYRIGHT='https://www.niddk.nih.gov/copyright'
EMBEDDER=HashingVectorizer(n_features=512,alternate_sign=False,norm='l2',ngram_range=(1,2),stop_words='english')
TOPICS={
 'What is Diabetes?':('Condition','diabetes',['diabetes','blood sugar','type 1','type 2','gestational','tieu duong']),
 'Symptoms & Causes':('Symptom','symptoms',['symptoms','thirst','urination','vision','fatigue','trieu chung']),
 'Risk Factors for Type 2 Diabetes':('RiskFactor','risk factors',['risk','family history','obesity','inactivity','nguy co']),
 'Preventing Type 2 Diabetes':('EducationalAction','prevention',['prevent','prevention','delay','phong ngua']),
 'Diabetes Tests & Diagnosis':('DiagnosticTest','screening tests',['tests','screening','diagnosis','diagnostic','xet nghiem']),
 'Managing Diabetes':('EducationalAction','care team',['care team','health care','professional','doctor','chuyen gia']),
 'Healthy Living with Diabetes':('LifestyleTopic','lifestyle',['lifestyle','meal','diet','physical activity','exercise','song lanh manh']),
 'Pregnancy & Diabetes':('Condition','gestational diabetes',['gestational','pregnancy','pregnant','thai ky']),
 'Other Types of Diabetes':('Condition','other diabetes',['other types']),
}
LABELS=('Condition','RiskFactor','Symptom','DiagnosticTest','LifestyleTopic','EducationalAction','Guideline','Source','DocumentChunk')

def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def validate_url(url):
 p=urlparse(str(url))
 if p.scheme!='https' or p.hostname!='www.niddk.nih.gov' or p.username or p.port or p.query or p.fragment: raise ValueError('SOURCE_NOT_ALLOWLISTED')
 return str(url)
def normalize(text): return re.sub(r'\s+',' ',text).strip()
def safe_text(text):
 return not re.search(r'ignore.{0,40}(instruction|rules)|system prompt|system:|developer:|<script|adjust.{0,20}dose|\b(metformin|insulin dose|dosage)\b',text,re.I)
def embedding(text): return EMBEDDER.transform([text]).toarray()[0].tolist()

def documents(fetch=False):
 DATA.mkdir(parents=True,exist_ok=True)
 for name,url in [('overview',URL),('copyright',COPYRIGHT)]:
  if fetch:
   with urlopen(validate_url(url),timeout=30) as response:
    validate_url(response.url); content=response.read()
   (DATA/(name+'.html')).write_bytes(content)
   (DATA/(name+'.retrieved')).write_text(datetime.now(timezone.utc).isoformat())
  if not (DATA/(name+'.html')).exists(): raise FileNotFoundError('Fetch source first')
 soup=BeautifulSoup((DATA/'overview.html').read_bytes(),'html.parser')
 title=soup.h1.get_text(' ',strip=True)
 retrieved=(DATA/'overview.retrieved').read_text() if (DATA/'overview.retrieved').exists() else datetime.fromtimestamp((DATA/'overview.html').stat().st_mtime,timezone.utc).isoformat()
 usage=BeautifulSoup((DATA/'copyright.html').read_bytes(),'html.parser').get_text(' ',strip=True)
 if 'majority' not in usage.lower() or 'copyright free' not in usage.lower(): raise ValueError('USAGE_POLICY_REVIEW_REQUIRED')
 chunks=[]
 for h in soup.select('h2'):
  section=h.get_text(' ',strip=True)
  if section not in TOPICS: continue
  paragraphs=h.parent.select('.dk-box-content p')
  if not paragraphs: raise ValueError('SOURCE_LAYOUT_CHANGED')
  label,entity,aliases=TOPICS[section]
  for paragraph in paragraphs:
   sentences=re.split(r'(?<=[.!?])\s+',normalize(paragraph.get_text(' ',strip=True)))
   for sentence in sentences:
    if not safe_text(sentence) or re.search(r'\b(medicines|medicine|drug|insulin|surgery)\b',sentence,re.I): continue
    if len(sentence)<30: continue
    # Sentence-preserving chunks, bounded to 1200 characters; never fabricate text.
    if len(sentence)>1200: raise ValueError('CHUNK_TOO_LONG_REVIEW_REQUIRED')
    identity=digest(URL+'|'+section+'|'+sentence)
    chunks.append(dict(id=identity,text=sentence,section=section,title=title,url=URL,publisher='NIDDK',retrieved_at=retrieved,
     publication_date=None,version=digest((DATA/'overview.html').read_bytes().hex()),usage_notes='NIDDK copyright policy: majority copyright free; text only, no logos/images/third-party material. '+COPYRIGHT,
     label=label,entity=entity,aliases=aliases,embedding=embedding(sentence)))
 if not chunks: raise ValueError('EMPTY_CORPUS')
 return chunks

class KnowledgeUnavailable(Exception): pass

class GraphStore:
 def __init__(self,uri=None,user=None,password=None):
  from backend.app.core.config import settings
  self.uri=uri or settings.neo4j_uri
  user=user if user is not None else settings.neo4j_user
  password=password if password is not None else settings.neo4j_password
  self.driver=GraphDatabase.driver(self.uri,auth=(user,password) if user and password else None,connection_timeout=3,max_transaction_retry_time=0)
 def close(self): self.driver.close()
 def read(self,query,**params):
  try:
   with self.driver.session(default_access_mode=READ_ACCESS) as session:
    return session.execute_read(lambda tx:[dict(r) for r in tx.run(query,**params)])
  except Exception: raise KnowledgeUnavailable('NEO4J_UNAVAILABLE') from None
 def summary(self):
  return {'nodes':self.read('MATCH (n) RETURN count(n) AS count')[0]['count'],'relationships':self.read('MATCH ()-[r]->() RETURN count(r) AS count')[0]['count'],'chunks':self.read('MATCH (n:DocumentChunk) RETURN count(n) AS count')[0]['count']}
 def ingest(self,chunks):
  with self.driver.session() as session:
   for label in LABELS:
    session.run(f'CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE').consume()
   session.run('CREATE INDEX chunk_section IF NOT EXISTS FOR (c:DocumentChunk) ON (c.section)').consume()
   def write(tx):
    for c in chunks:
     label=c['label']; assert label in LABELS
     source={k:c[k] for k in ['title','url','publisher','retrieved_at','publication_date','version','usage_notes']}
     tx.run('MERGE (s:Source {id:$url}) SET s += $source MERGE (g:Guideline {id:$url}) SET g.kind="patient education overview",g.title=$title MERGE (g)-[:REFERENCES]->(s)',url=c['url'],title=c['title'],source=source).consume()
     tx.run('MATCH (s:Source {id:$url}) MERGE (c:DocumentChunk {id:$id}) SET c += $props MERGE (s)-[:HAS_CHUNK]->(c)',url=c['url'],id=c['id'],props={k:v for k,v in c.items() if k not in ['label','aliases']}).consume()
     tx.run(f'MATCH (c:DocumentChunk {{id:$id}}) MERGE (e:{label} {{id:$entity}}) SET e.name=$entity,e.aliases=$aliases MERGE (e)-[:SUPPORTED_BY]->(c) MERGE (d:Condition {{id:"diabetes"}}) SET d.name="diabetes" MERGE (d)-[:RELATED_TO]->(e)',id=c['id'],entity=c['entity'],aliases=c['aliases']).consume()
   session.execute_write(write)
  return self.summary()
 def candidates(self,entities=None):
  if entities is None:
   return self.read('MATCH (c:DocumentChunk) RETURN properties(c) AS c ORDER BY c.id LIMIT $limit',limit=1000)
  return self.read('MATCH (e)-[:SUPPORTED_BY]->(c:DocumentChunk) WHERE e.id IN $entities RETURN DISTINCT properties(c) AS c ORDER BY c.id LIMIT $limit',entities=entities,limit=1000)
