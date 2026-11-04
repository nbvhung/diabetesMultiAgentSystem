"""Namespaced, provenance-bearing diabetes graph; no user Cypher or old graph mutation."""
from dataclasses import dataclass
from backend.app.knowledge.store import GraphStore,KnowledgeUnavailable

# Curated extraction rules tie a domain relation to a designated source and exact
# supporting passage. These are auditable education assertions, not inferred causality.
@dataclass(frozen=True)
class AssertionRule:
    subject:str
    predicate:str
    object:str
    source:str
    section:str
    quote:str


ASSERTIONS=[
 AssertionRule('type2','HAS_RISK_FACTOR','obesity','risk','What are the risk factors for type 2 diabetes?','are overweight or have obesity .'),
 AssertionRule('type2','HAS_RISK_FACTOR','family_history','risk','What are the risk factors for type 2 diabetes?','have a family history of diabetes.'),
 AssertionRule('type2','HAS_RISK_FACTOR','physical_inactivity','risk','What are the risk factors for type 2 diabetes?','are not physically active, because of physical limitations, a sedentary lifestyle, or a job that requires sitting for long periods of time.'),
 AssertionRule('diabetes','HAS_SYMPTOM','thirst','symptoms','What are the symptoms of diabetes?','feeling very thirsty'),
 AssertionRule('diabetes','HAS_SYMPTOM','frequent_urination','symptoms','What are the symptoms of diabetes?','increased urination'),
 AssertionRule('diabetes','HAS_SYMPTOM','fatigue','symptoms','What are the symptoms of diabetes?','blurred vision fatigue sores that do not heal'),
 AssertionRule('diabetes','SCREENED_WITH','a1c','tests','A1C test','Before using the A1C test to diagnose diabetes, your doctor will consider factors'),
 AssertionRule('diabetes','SCREENED_WITH','fasting_glucose','tests','Fasting plasma glucose test','The fasting plasma glucose (FPG) test measures your blood glucose level at a single point in time.'),
 AssertionRule('diabetes','HAS_COMPLICATION','neuropathy','neuropathy','What Is Diabetic Neuropathy?','Diabetic neuropathy is nerve damage that is caused by diabetes.'),
 AssertionRule('diabetes','HAS_COMPLICATION','retinopathy','eye','Diabetic retinopathy','Damaged blood vessels can harm the retina, causing a disease called diabetic retinopathy.'),
 AssertionRule('diabetes','HAS_COMPLICATION','foot_problems','foot','How can diabetes affect my feet?','Diabetes also can lower the amount of blood flow in your feet.'),
]
PREDICATES={a.predicate for a in ASSERTIONS}


def supported_assertions(chunks,release):
    assertions=[]
    for rule in ASSERTIONS:
        # A topic/keyword match is insufficient for a graph fact. Require the exact
        # reviewed clause in its designated source and section, with parent context.
        candidates=[c for c in chunks if c['source_id']==rule.source and c['section']==rule.section and rule.quote in c['text']]
        if not candidates:continue
        c=min(candidates,key=lambda chunk:(len(chunk['text']),chunk['id']))
        assertions.append({'id':release+':'+rule.subject+':'+rule.predicate+':'+rule.object,'subject':rule.subject,'predicate':rule.predicate,'object':rule.object,'evidence_id':c['id'],'release':release,'extraction_rule':'curated-exact-source-clause-2.0','supporting_quote':rule.quote,'section_context':c.get('section_context',c['section'])})
    return assertions


class DiabetesGraph:
    def __init__(self,store=None):self.store=store or GraphStore()
    def candidates(self,release,topics=None):
        if not hasattr(self.store,'read'):raise KnowledgeUnavailable('NEO4J_UNAVAILABLE')
        if topics is None:
            rows=self.store.read('MATCH (c:DiabetesEvidence {release:$release}) RETURN c.id AS id ORDER BY c.id LIMIT 2000',release=release)
        else:
            rows=self.store.read('MATCH (t:DiabetesTopic)-[:SUPPORTED_BY]->(c:DiabetesEvidence {release:$release}) WHERE t.id IN $topics RETURN DISTINCT c.id AS id ORDER BY id LIMIT 2000',release=release,topics=topics)
        return [r['id'] for r in rows]
    def summary(self,release=None):
        if not hasattr(self.store,'read'):raise KnowledgeUnavailable('NEO4J_UNAVAILABLE')
        if release is None:
            from .corpus import Corpus
            corpus=Corpus();corpus.load();release=corpus.manifest['chunks_sha256']
        rows=self.store.read('MATCH (c:DiabetesEvidence {release:$release}) RETURN count(c) AS chunks,count(DISTINCT c.source_id) AS sources,collect(DISTINCT c.release) AS releases',release=release)
        assertions=self.store.read('MATCH (a:DiabetesAssertion {release:$release}) RETURN count(a) AS count',release=release)[0]['count']
        return {**rows[0],'supported_assertions':assertions}
    def ingest(self,corpus):
        corpus.load();release=corpus.manifest['chunks_sha256'];chunks=corpus.chunks
        assertions=supported_assertions(chunks,release)
        with self.store.driver.session() as session:
            for label in ['DiabetesSource','DiabetesEvidence','DiabetesTopic','DiabetesConcept','DiabetesAssertion']:
                session.run(f'CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE').consume()
            def write(tx):
                # Retire only this namespace; old release nodes remain audit history.
                for c in chunks:
                    props={**c,'release':release};props['topics']=list(c['topics'])
                    tx.run('MERGE (s:DiabetesSource {id:$source_id}) SET s.url=$url,s.title=$title,s.publisher="NIDDK",s.version=$version MERGE (c:DiabetesEvidence {id:$id}) SET c += $props MERGE (s)-[:HAS_CHUNK]->(c) WITH c UNWIND $topics AS topic MERGE (t:DiabetesTopic {id:topic}) MERGE (t)-[:SUPPORTED_BY]->(c)',source_id=c['source_id'],url=c['url'],title=c['title'],version=c['source_sha256'],id=c['id'],props=props,topics=c['topics']).consume()
                for a in assertions:
                    assert a['predicate'] in PREDICATES
                    # Replace only this generated assertion's support/direct edge.
                    # Reseeding must not keep a superseded, weaker supporting passage.
                    tx.run('MATCH (a:DiabetesAssertion {id:$id})-[r:SUPPORTED_BY]->(:DiabetesEvidence) DELETE r',id=a['id']).consume()
                    tx.run(f'MATCH (s:DiabetesConcept {{id:$subject}})-[r:{a["predicate"]}]->(o:DiabetesConcept {{id:$object}}) WHERE r.release=$release DELETE r',subject=a['subject'],object=a['object'],release=release).consume()
                    tx.run(f'MATCH (c:DiabetesEvidence {{id:$evidence_id}}) MERGE (s:DiabetesConcept {{id:$subject}}) MERGE (o:DiabetesConcept {{id:$object}}) MERGE (a:DiabetesAssertion {{id:$id}}) SET a += $props MERGE (a)-[:SUPPORTED_BY]->(c) MERGE (s)-[:SUBJECT_OF]->(a) MERGE (a)-[:OBJECT]->(o) MERGE (s)-[r:{a["predicate"]} {{evidence_id:$evidence_id}}]->(o) SET r.release=$release',**{k:v for k,v in a.items() if k!='extraction_rule'},props=a).consume()
            session.execute_write(write)
        return {'release':release,'chunks':len(chunks),'sources':corpus.manifest['source_count'],'assertions':assertions,'graph':self.summary()}
