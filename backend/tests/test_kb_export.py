"""Verify escaping and source-grounded exports; live import has its own verifier."""
from pathlib import Path
from backend.app.research.corpus import Corpus
from backend.app.research.kb_export import export, literal, statements
from backend.app.research.graph import supported_assertions


def test_export_is_deterministic_and_bound_to_actual_corpus(tmp_path):
    corpus = Corpus()
    first = export(corpus, tmp_path / 'first.cypher')
    second = export(corpus, tmp_path / 'second.cypher')
    assert first == second
    content = (tmp_path / 'first.cypher').read_text(encoding='utf-8')
    assertions = supported_assertions(corpus.chunks, first['release'])
    assert len(assertions) >= 5
    for a in assertions:
        assert a['supporting_quote'] in corpus.by_id[a['evidence_id']]['text']
        assert literal(a['id']) in content
    assert len(list(statements(corpus))) == 5 + len(corpus.chunks) + len(assertions)
    assert first['chunks'] == corpus.manifest['chunk_count']


def test_cypher_literals_escape_untrusted_document_text():
    assert literal('quote " newline\n slash \\') == '"quote \\" newline\\n slash \\\\"'
    assert literal({'odd`key': None}) == '{`odd``key`:null}'
    assert literal([True, 1, 'x']) == '[true,1,"x"]'
