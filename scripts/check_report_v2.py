"""Real Neo4j import/readback in a rolled-back transaction; preserve existing DB."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.research.corpus import Corpus
from backend.app.research.graph import DiabetesGraph, supported_assertions
from backend.app.research.kb_export import export, statements


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Execute Neo4j queries with transaction rollback')
    args = parser.parse_args()
    out = ROOT / 'docs/validation/report_v2'
    out.mkdir(parents=True, exist_ok=True)
    corpus = Corpus()
    result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'export': export(corpus, ROOT / 'kb_diabetes.cypher'),
              'live_import': 'NOT_RUN', 'clinical_validation': False}
    if args.live:
        graph = DiabetesGraph()
        try:
            release = corpus.manifest['chunks_sha256']
            expected = supported_assertions(corpus.chunks, release)
            with graph.store.driver.session() as session:
                tx = session.begin_transaction()
                try:
                    # Run the exact exported DML, not a replacement seed implementation.
                    queries = list(statements(corpus))[5:]
                    def snapshot():
                        chunks = tx.run('MATCH (c:DiabetesEvidence {release:$r}) RETURN properties(c) AS p ORDER BY c.id', r=release).data()
                        assertions = tx.run('MATCH (a:DiabetesAssertion {release:$r})-[:SUPPORTED_BY]->(c:DiabetesEvidence) RETURN properties(a) AS p,c.id AS evidence_id ORDER BY a.id', r=release).data()
                        edges = tx.run('MATCH (:DiabetesConcept)-[r]->(:DiabetesConcept) WHERE r.release=$r RETURN count(r) AS n', r=release).single()['n']
                        return chunks, assertions, edges
                    for query in queries:
                        tx.run(query).consume()
                    first = snapshot()
                    for query in queries:
                        tx.run(query).consume()
                    assert snapshot() == first, 'IMPORT_NOT_IDEMPOTENT'
                    assert len(first[0]) == len(corpus.chunks)
                    assert len(first[1]) == len(expected)
                    assert first[2] == len(expected)
                    assert {row['p']['id']:row['p'] for row in first[0]} == {c['id']:dict(c,release=release) for c in corpus.chunks}
                    assert {row['p']['id']:row['p'] for row in first[1]} == {a['id']:a for a in expected}
                    result['live_import'] = 'PASS'
                    result['idempotent_import'] = 'PASS'
                    result['exact_property_readback'] = 'PASS'
                    result['transaction'] = 'ROLLED_BACK'
                finally:
                    tx.rollback()
        finally:
            graph.store.close()
    result['files'] = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['kb_diabetes.cypher','kb_diabetes_queries.cypher','backend/app/research/kb_export.py']}
    (out/'kb_checks.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
