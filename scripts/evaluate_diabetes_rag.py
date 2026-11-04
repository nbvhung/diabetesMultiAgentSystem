"""Same 80 bilingual questions/corpus/tools across four retrieval strategies."""
from phase07_common import *
import statistics,time
from backend.app.research.corpus import Corpus
from backend.app.research.graph import DiabetesGraph
from backend.app.research.retrieval import Retriever


def questions(corpus):
    config=json.loads((ROOT/'experiments/configs/diabetes_benchmark.json').read_text(encoding='utf-8'))
    confirmatory=json.loads((ROOT/'experiments/configs/diabetes_confirmatory_questions.json').read_text(encoding='utf-8'))['questions']
    result=[]
    for family in config['families']:
        relevant={c['id'] for c in corpus.chunks if c['source_id'] in family['source_ids'] and any(section.casefold() in c['section'].casefold() for section in family['section_contains'])}
        if not relevant:raise ValueError('Ground-truth source/section no longer exists: '+family['id'])
        for index,question in enumerate(family['queries']):
            result.append({'id':family['id']+':'+str(index),'family':family['id'],'language':'vi' if index%2==0 else 'en','split':'development' if index<2 else 'diagnostic_phrasing','question':question,'relevant_ids':sorted(relevant)})
        for index,question in enumerate(confirmatory[family['id']]):
            result.append({'id':family['id']+':confirmatory:'+str(index),'family':family['id'],'language':'vi' if index==0 else 'en','split':'confirmatory_phrasing','question':question,'relevant_ids':sorted(relevant)})
    for index,question in enumerate(config['unanswerable']):result.append({'id':'empty:'+str(index),'family':'unanswerable','language':'mixed','split':'unanswerable','question':question,'relevant_ids':[]})
    return result


def main():
    corpus=Corpus();corpus.load();graph=DiabetesGraph();retriever=Retriever(graph,corpus)
    gold=questions(corpus);rows=[];summary=[]
    try:
        retriever.prepare();retriever.encoder.load();retriever.semantic_index()
        # All strategies share the same data. No old-corpus/new-corpus metric comparison.
        for item in gold:
            for strategy in ['lexical','semantic','graph','hybrid']:
                started=time.perf_counter();output=retriever.search(item['question'],strategy=strategy);latency=(time.perf_counter()-started)*1000
                ids=[e.evidence_id for e in output.evidence];relevant=set(item['relevant_ids']);hits=[i in relevant for i in ids]
                correct=sum(corpus.admits(e) for e in output.evidence)
                rows.append({'strategy':strategy,'question_id':item['id'],'family':item['family'],'language':item['language'],'split':item['split'],'retrieved_ids':ids,'relevant_ids':sorted(relevant),'recall_at_3':len(set(ids)&relevant)/len(relevant) if relevant else None,'precision_at_returned':sum(hits)/len(ids) if ids and relevant else 0.0 if relevant else None,'rr_at_3':next((1/(i+1) for i,hit in enumerate(hits) if hit),0) if relevant else None,'correct_citations':correct,'citation_count':len(ids),'no_evidence_correct':int(not ids) if not relevant else None,'latency_ms':latency,'semantic_used':output.semantic_available,'reranker_used':output.reranker_available})
    finally:graph.store.close()
    for split in ['development','diagnostic_phrasing','confirmatory_phrasing']:
        for strategy in ['lexical','semantic','graph','hybrid']:
            group=[r for r in rows if r['strategy']==strategy and r['split']==split]
            count=sum(r['citation_count'] for r in group)
            summary.append({'strategy':strategy,'split':split,'queries':len(group),'recall_at_3':statistics.mean(r['recall_at_3'] for r in group),'precision_at_returned':statistics.mean(r['precision_at_returned'] for r in group),'mrr_at_3':statistics.mean(r['rr_at_3'] for r in group),'citation_provenance':sum(r['correct_citations'] for r in group)/count if count else None,'latency_ms':statistics.mean(r['latency_ms'] for r in group)})
    heldout=[r for r in summary if r['split']=='confirmatory_phrasing']
    plot_bars('diabetes_rag',heldout,'strategy',['precision_at_returned','mrr_at_3','latency_ms'],'Diabetes corpus 2.0 / 40 confirmatory bilingual phrasings; source-section relevance')
    save('diabetes_rag',summary,rows,'125 project-authored SYNTHETIC questions; 40 confirmatory phrasings fixed after architecture selection. Coarse target source-section relevance, not clinical correctness.',datasets=['experiments/configs/diabetes_benchmark.json','experiments/configs/diabetes_confirmatory_questions.json','experiments/configs/diabetes_sources.json','data/knowledge/diabetes-v2/manifest.json','artifacts/embeddings/diabetes-minilm-1.0/manifest.json','artifacts/embeddings/diabetes-minilm-1.0/corpus_index.json','artifacts/embeddings/diabetes-reranker-1.0/manifest.json'],config={'k_max':3,'strategies':['lexical','semantic','graph','hybrid'],'thresholds':'semantic cosine >=.25 and combined >=.23; pure semantic >=.30; lexical cosine >=.055; hybrid reranker sigmoid >=.35, top16 pool, relative cutoff .25','encoder':'paraphrase-multilingual-MiniLM-L12-v2, actual CPU inference','reranker':'mmarco-mMiniLMv2-L12-H384-v1, actual CPU inference for hybrid only','source_diversity':'max 2 per source','labels':'manual target source IDs + section substrings, expanded to chunk IDs; semantically valid passages in other sections can be false negatives','split':'Original 80 queries used during development/diagnosis. New 40 confirmatory phrasings fixed after cross-encoder selection; overlapping topics/sources; no external clinical validation'})

if __name__=='__main__':main()
