"""E2 uses the same fixed queries and actual Neo4j corpus in all strategies."""
from phase07_common import *
import statistics, time
from backend.app.knowledge.store import GraphStore, documents
from backend.app.rag.retrieval import Retrieval


def main():
    corpus={c['id']:c for c in documents()}
    gold=json.loads((ROOT/'experiments/configs/knowledge_eval.json').read_text())
    store=GraphStore(); summary=[]; rows=[]
    try:
        store.driver.verify_connectivity()
        for strategy in ['vector','graph','hybrid']:
            for query in gold:
                relevant={k for k,c in corpus.items() if c['section'] in query['relevant_sections']}
                start=time.perf_counter(); evidence=Retrieval(store,strategy).search(query['question'],5); latency=(time.perf_counter()-start)*1000
                ids=[e.evidence_id for e in evidence]
                correct=sum(e.evidence_id in corpus and str(e.source_url)==corpus[e.evidence_id]['url'] and e.excerpt==corpus[e.evidence_id]['text'] for e in evidence)
                rows.append({'strategy':strategy,'question_id':query['id'],'relevant_ids':sorted(relevant),'retrieved_ids':ids,'recall_at_5':len(set(ids)&relevant)/len(relevant) if relevant else None,'rr_at_5':next((1/(i+1) for i,x in enumerate(ids) if x in relevant),0) if relevant else None,'citation_count':len(ids),'correct_citations':correct,'no_evidence_correct':int(not ids) if not relevant else None,'latency_ms':latency})
            selected=[r for r in rows if r['strategy']==strategy]; answerable=[r for r in selected if r['relevant_ids']]
            count=sum(r['citation_count'] for r in selected)
            summary.append({'strategy':strategy,'recall_at_5':statistics.mean(r['recall_at_5'] for r in answerable),'mrr_at_5':statistics.mean(r['rr_at_5'] for r in answerable),'citation_correctness':sum(r['correct_citations'] for r in selected)/count if count else None,'citation_count':count,'no_evidence_accuracy':statistics.mean(r['no_evidence_correct'] for r in selected if not r['relevant_ids']),'latency_ms':statistics.mean(r['latency_ms'] for r in selected)})
    finally: store.close()
    plot_bars('rag',summary,'strategy',['recall_at_5','mrr_at_5','latency_ms'],'E2 / actual Neo4j retrieval on 24 project-authored questions')
    save('rag',summary,rows,'Project-authored 24-question benchmark. Citation correctness checks exact excerpt/URL provenance, not clinical entailment.',datasets=['experiments/configs/knowledge_eval.json','data/knowledge/overview.html','data/knowledge/copyright.html'],config={'k':5,'strategies':['vector','graph','hybrid'],'embedding':'512-feature HashingVectorizer; lexical vector, not dense semantic model','relevance':'manual section-level labels','latency':'one pass, includes database reads and embedding; local hardware'})

if __name__=='__main__':main()
