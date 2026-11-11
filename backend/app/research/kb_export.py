"""Portable Neo4j export of the verified runtime corpus, without APOC or secrets."""
import hashlib
import json
from .graph import PREDICATES, supported_assertions


def literal(value):
    if value is None:
        return 'null'
    if isinstance(value, dict):
        return '{' + ','.join('`' + key.replace('`', '``') + '`:' + literal(v) for key, v in value.items()) + '}'
    if isinstance(value, (list, tuple)):
        return '[' + ','.join(literal(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=False)


def statements(corpus):
    corpus.load()
    release = corpus.manifest['chunks_sha256']
    for label in ('DiabetesSource', 'DiabetesEvidence', 'DiabetesTopic', 'DiabetesConcept', 'DiabetesAssertion'):
        yield f'CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE'
    for c in corpus.chunks:
        props = dict(c, release=release)
        yield ('MERGE (s:DiabetesSource {id:' + literal(c['source_id']) + '}) '
               'SET s += ' + literal(dict(url=c['url'], title=c['title'], publisher=c['publisher'], version=c['source_sha256'])) + ' '
               'MERGE (c:DiabetesEvidence {id:' + literal(c['id']) + '}) SET c += ' + literal(props) + ' '
               'MERGE (s)-[:HAS_CHUNK]->(c) WITH c UNWIND ' + literal(c['topics']) + ' AS topic '
               'MERGE (t:DiabetesTopic {id:topic}) MERGE (t)-[:SUPPORTED_BY]->(c)')
    for a in supported_assertions(corpus.chunks, release):
        if a['predicate'] not in PREDICATES:
            raise ValueError('UNREGISTERED_PREDICATE')
        yield ('MATCH (c:DiabetesEvidence {id:' + literal(a['evidence_id']) + '}) '
               'MERGE (s:DiabetesConcept {id:' + literal(a['subject']) + '}) '
               'MERGE (o:DiabetesConcept {id:' + literal(a['object']) + '}) '
               'MERGE (a:DiabetesAssertion {id:' + literal(a['id']) + '}) SET a += ' + literal(a) + ' '
               'MERGE (a)-[:SUPPORTED_BY]->(c) MERGE (s)-[:SUBJECT_OF]->(a) MERGE (a)-[:OBJECT]->(o) '
               'MERGE (s)-[r:' + a['predicate'] + ' {evidence_id:' + literal(a['evidence_id']) + ' }]->(o) '
               'SET r.release=' + literal(release))


def export(corpus, target):
    queries = list(statements(corpus))
    content = ('// Generated from checksum-verified NIDDK corpus. Education only; no patient records.\n'
               '// Import into a fresh Neo4j database with cypher-shell -f kb_diabetes.cypher\n'
               '// Repeated imports of this release are idempotent. No DELETE, APOC or credentials.\n'
               + ';\n'.join(queries) + ';\n')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8', newline='\n')
    return {'release': corpus.manifest['chunks_sha256'], 'sources': corpus.manifest['source_count'],
            'chunks': len(corpus.chunks), 'assertions': len(supported_assertions(corpus.chunks, corpus.manifest['chunks_sha256'])),
            'statements': len(queries), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
