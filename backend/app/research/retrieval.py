"""Diabetes-focused multilingual retrieval, graph routing, reranking and abstention."""
from pathlib import Path
from threading import RLock
import hashlib,json,re,unicodedata
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .schemas import Evidence,KnowledgeOutput
from .corpus import Corpus
from .semantic import SemanticEncoder,SemanticUnavailable
from .reranker import Reranker


def norm(text):return ''.join(c for c in unicodedata.normalize('NFKD',text.lower().replace('đ','d')) if not unicodedata.combining(c))

TOPICS={
 'symptoms':('symptoms thirst frequent urination fatigue blurred vision',['trieu chung','dau hieu','khat nuoc','tieu nhieu','met moi','symptom','symptoms','thirst','urination','fatigue','blurred vision']),
 'risk':('type 2 diabetes risk factors family history obesity physical inactivity',['yeu to nguy co','nguy co','risk','family history','tien su gia dinh','beo phi','obesity','overweight','thua can']),
 'prevention':('prevent delay type 2 diabetes',['phong ngua','phong tranh','ngan ngua','prevent','prevention','delay']),
 'tests':('diabetes blood tests A1C fasting glucose diagnosis',['xet nghiem','a1c','hba1c','tests','test','testing','diagnosis','fasting glucose','duong huyet luc doi']),
 'nutrition':('healthy diabetes eating meal plan carbohydrate fiber food',['dinh duong','an uong','an gi','thuc pham','tinh bot','chat xo','nutrition','meal','meals','diet','food','foods','carbohydrate','carbohydrates','fiber']),
 'activity':('diabetes physical activity exercise walking',['van dong','tap the duc','di bo','hoat dong the chat','activity','exercise','walking']),
 'monitoring':('diabetes blood glucose monitoring blood sugar meter continuous glucose',['theo doi','do duong huyet','monitor','monitoring','glucose meter','continuous glucose','cgm']),
 'management':('diabetes management care team health professional',['quan ly','kiem soat','cham soc','management','care team','health professional']),
 'type1':('type 1 diabetes autoimmune immune system insulin',['typ 1','type 1','loai 1','tuy 1','tuyp 1']),
 'type2':('type 2 diabetes insulin resistance',['typ 2','type 2','loai 2','tuyp 2']),
 'types':('different types diabetes type 1 type 2 gestational',['cac loai','phan loai','types','khac nhau','difference','differences']),
 'prediabetes':('prediabetes higher than normal blood glucose',['tien dai thao duong','tien tieu duong','prediabetes']),
 'insulin_resistance':('insulin resistance cells respond insulin',['khang insulin','insulin resistance','insulin resistant']),
 'gestational':('gestational diabetes pregnancy',['thai ky','mang thai','gestational','pregnancy','pregnant']),
 'neuropathy':('diabetic neuropathy nerve damage numbness',['than kinh','te bi','neuropathy','nerve damage','numbness']),
 'foot':('diabetes foot problems foot care neuropathy',['ban chan','cham soc chan','vet loet chan','foot','feet']),
 'eye':('diabetic eye disease retinopathy vision',['bien chung mat','vong mac','retinopathy','eye','eyes']),
 'complications':('diabetes complications eyes kidneys nerves heart',['bien chung','complication','complications']),
 'causes':('diabetes causes insulin pancreas immune system',['nguyen nhan','causes','cause','pancreas','tuyen tuy']),
}


def query_topics(question):
    value=norm(question)
    topics=[key for key,(_,aliases) in TOPICS.items() if any(re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',value) for alias in aliases)]
    if set(topics)-{'type1','type2','types'}:topics=[t for t in topics if t not in ('type1','type2','types')]
    # Specific diabetes type questions retain that context, not just generic symptoms.
    if not topics and re.search(r'(what is|define|explain|about|la gi|tim hieu|giai thich).{0,25}(diabetes|tieu duong|dai thao duong)|(diabetes|tieu duong|dai thao duong).{0,15}la gi',value):topics=['diabetes']
    if not topics and re.search(r'\b(diabetes|tieu duong|dai thao duong|glucose|insulin|duong huyet)\b',value):topics=['diabetes']
    if re.search(r'python|crypto|football|weather|lung cancer|ung thu phoi|quantum|tu vi|chung khoan',value):return []
    return topics


RETRY_QUESTIONS={
 'symptoms':'What are the common symptoms of diabetes?',
 'risk':'What are the risk factors for type 2 diabetes?',
 'prevention':'How can people prevent or delay type 2 diabetes?',
 'tests':'What blood tests are used to diagnose diabetes?',
 'nutrition':'What does healthy eating with diabetes involve?',
 'activity':'How can physical activity help manage diabetes?',
 'monitoring':'How is blood glucose monitored in diabetes?',
 'management':'How can people manage diabetes with a health care team?',
 'type1':'What is type 1 diabetes?', 'type2':'What is type 2 diabetes?',
 'types':'What are the different types of diabetes?',
 'prediabetes':'What is prediabetes?',
 'insulin_resistance':'What is insulin resistance?',
 'gestational':'What is gestational diabetes?',
 'neuropathy':'What is diabetic neuropathy?',
 'foot':'How can diabetes affect the feet?',
 'eye':'How can diabetes affect the eyes?',
 'complications':'What health problems can diabetes cause?',
 'causes':'What causes diabetes?', 'diabetes':'What is diabetes?',
}


def rewrite_query(question,topics,*,retry=False):
    # Bounded, inspectable bilingual expansion; no arbitrary tool arguments or Cypher.
    # A retry asks a natural-language question for the same detected topic. The
    # original user question remains the composition/review target, so the rewrite
    # cannot authorize an irrelevant generated claim or personal advice.
    if retry and topics:return ' '.join(RETRY_QUESTIONS[t] for t in topics if t in RETRY_QUESTIONS)
    return question+' '+ ' '.join(TOPICS[t][0] if t in TOPICS else 'what is diabetes blood glucose' for t in topics)


class Retriever:
    def __init__(self,store,corpus=None,encoder=None,reranker=None):
        self.store=store;self.corpus=corpus or Corpus();self.encoder=encoder or SemanticEncoder();self.lock=RLock();self.ready=False
        self.reranker=reranker or Reranker()
    def prepare(self):
        with self.lock:
            if self.ready:return
            self.corpus.load();self.rows=self.corpus.chunks
            self.tfidf=TfidfVectorizer(ngram_range=(1,2),stop_words='english',sublinear_tf=True)
            self.lexical=self.tfidf.fit_transform([c['section']+' '+c['text'] for c in self.rows])
            self.ids={c['id']:i for i,c in enumerate(self.rows)};self.vectors=None
            self.ready=True
    def semantic_index(self):
        if self.vectors is not None:return self.vectors
        path=self.encoder.path
        meta=json.loads((path/'corpus_index.json').read_text(encoding='utf-8'))
        if meta['corpus_sha256']!=self.corpus.manifest['chunks_sha256'] or meta['encoder_manifest_sha256']!=hashlib.sha256((path/'manifest.json').read_bytes()).hexdigest() or meta['vectors_sha256']!=hashlib.sha256((path/'corpus_vectors.npz').read_bytes()).hexdigest():raise SemanticUnavailable('SEMANTIC_INDEX_MISMATCH')
        with np.load(path/'corpus_vectors.npz',allow_pickle=False) as data:
            vectors=data['vectors'].copy();ids=data['ids'].tolist()
        if ids!=[c['id'] for c in self.rows] or vectors.shape!=(len(ids),384) or not np.isfinite(vectors).all():raise SemanticUnavailable('SEMANTIC_INDEX_INVALID')
        vectors.flags.writeable=False;self.vectors=vectors
        return self.vectors
    def search(self,question,query=None,attempt=1,strategy='hybrid',k=3):
        if strategy not in ('lexical','semantic','graph','hybrid') or not 1<=k<=5:raise ValueError('Unknown retrieval configuration')
        self.prepare();topics=query_topics(question)
        if not topics:return KnowledgeOutput(evidence=[],query_topics=[],coverage=0,adequate=False,semantic_available=False,retrieval_method='domain_clarification',attempt=attempt)
        release=self.corpus.manifest['chunks_sha256']
        all_ids=set(self.store.candidates(release,None))
        graph_ids=set(self.store.candidates(release,topics))
        available=[self.ids[i] for i in sorted(all_ids) if i in self.ids]
        if not available:return KnowledgeOutput(evidence=[],query_topics=topics,coverage=0,adequate=False,semantic_available=False,retrieval_method='graph_empty',attempt=attempt)
        ranking_query=query if attempt>1 and query else question
        expanded=rewrite_query(query or question,topics)
        lexical=np.asarray((self.lexical@self.tfidf.transform([expanded]).T).toarray()).ravel()
        dense=np.zeros(len(self.rows));semantic=False
        if strategy in ('semantic','hybrid'):
            try:dense=self.semantic_index()@self.encoder.encode([ranking_query])[0];semantic=True
            except (SemanticUnavailable,OSError,ValueError,KeyError):pass
        candidates=[]
        for index in available:
            chunk=self.rows[index];graph=chunk['id'] in graph_ids
            # Specific topics require a graph-supported source, preventing general
            # diabetes passages outranking a relevant topic through broad keyword overlap.
            if strategy in ('graph','hybrid') and not graph:continue
            topic_overlap=len(set(topics)&set(chunk['topics']))/len(topics)
            if topics==['diabetes']:topic_overlap=1.0
            lex=float(lexical[index]);sem=max(0,float(dense[index]))
            if strategy=='lexical':score=min(1,lex)
            elif strategy=='semantic':score=sem
            elif strategy=='graph':score=.7*min(1,lex)+.3*topic_overlap
            elif semantic:score=.65*sem+.25*min(1,lex)+.1*topic_overlap
            else:score=.85*min(1,lex)+.15*topic_overlap
            # Thresholds are declared retrieval policy, not calibrated probabilities.
            # Record them for held-out evaluation; do not fill k with unrelated chunks.
            admitted=(sem>=.25 and score>=.23) if semantic else lex>=.055
            if strategy=='semantic':admitted=sem>=.30
            if admitted:candidates.append((score,index))
        candidates.sort(key=lambda x:(-x[0],self.rows[x[1]]['id']))
        reranked=False
        if strategy=='hybrid' and candidates:
            try:
                pool=candidates[:16]
                scores=self.reranker.score(ranking_query,[self.rows[i].get('section_context',self.rows[i]['section'])+' / '+self.rows[i]['text'] for _,i in pool])
                if scores.shape!=(len(pool),) or not np.isfinite(scores).all():raise SemanticUnavailable('RERANKER_INVALID_SCORES')
                # Sigmoid logits are ranking signals, not calibrated clinical probabilities.
                candidates=[(float(score),index) for score,(_,index) in zip(scores,pool) if score>=.35]
                candidates.sort(key=lambda x:(-x[0],self.rows[x[1]]['id']));reranked=True
            except (SemanticUnavailable,OSError,ValueError):pass
        selected=[];per_source={};best=candidates[0][0] if candidates else 0
        for score,index in candidates:
            chunk=self.rows[index]
            if score<best-(.25 if reranked else .16) or per_source.get(chunk['source_id'],0)>=2:continue
            # Avoid near-identical repeated passages consuming the evidence budget.
            if any(chunk['text']==self.rows[i]['text'] for _,i in selected):continue
            selected.append((score,index));per_source[chunk['source_id']]=per_source.get(chunk['source_id'],0)+1
            if len(selected)>=k:break
        evidence=[]
        for score,index in selected:
            c=self.rows[index]
            evidence.append(Evidence(evidence_id=c['id'],source_id=c['source_id'],source_title=c['title'],source_url=c['url'],section=c['section'],section_context=c.get('section_context'),excerpt=c['text'],retrieved_at=c['retrieved_at'],source_version=c['source_sha256'],topics=c['topics'],retrieval_score=min(1,max(0,score)),last_reviewed=c['last_reviewed']))
        covered={t for e in evidence for t in e.topics};coverage=len(set(topics)&covered)/len(topics)
        method='hybrid_cross_encoder' if reranked else strategy if semantic or strategy in ('graph','lexical') else strategy+'_lexical_fallback'
        return KnowledgeOutput(evidence=evidence,query_topics=topics,coverage=coverage,adequate=bool(evidence) and coverage==1.0,semantic_available=semantic,retrieval_method=method,attempt=attempt,reranker_available=reranked)
