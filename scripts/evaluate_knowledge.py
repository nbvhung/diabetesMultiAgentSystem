from pathlib import Path
import sys,json,time,statistics
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.knowledge.store import GraphStore,documents
from backend.app.rag.retrieval import Retrieval
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 gold=json.loads((ROOT/'experiments/configs/knowledge_eval.json').read_text())
 corpus={c['id']:c for c in documents()}; store=GraphStore(); output={}
 try:
  for strategy in ['vector','graph','hybrid']:
   rows=[]
   for item in gold:
    relevant={k for k,c in corpus.items() if c['section'] in item['relevant_sections']}
    start=time.perf_counter(); evidence=Retrieval(store,strategy).search(item['question'],5); latency=(time.perf_counter()-start)*1000
    hits=[e.evidence_id in relevant for e in evidence]
    correct=[e.evidence_id in corpus and corpus[e.evidence_id]['text']==e.excerpt and corpus[e.evidence_id]['url']==str(e.source_url) for e in evidence]
    rows.append(dict(**item,relevant_ids=sorted(relevant),retrieved_ids=[e.evidence_id for e in evidence],recall_at_5=len(set(e.evidence_id for e in evidence)&relevant)/len(relevant) if relevant else None,reciprocal_rank=next((1/(i+1) for i,v in enumerate(hits) if v),0) if relevant else None,citation_correct=all(correct),citation_count=len(correct),no_evidence_correct=(not evidence) if not relevant else None,latency_ms=latency))
   answerable=[x for x in rows if x['relevant_ids']]; empty=[x for x in rows if not x['relevant_ids']]
   output[strategy]={'recall_at_5':statistics.mean(x['recall_at_5'] for x in answerable),'mrr_at_5':statistics.mean(x['reciprocal_rank'] for x in answerable),'citation_provenance_correctness':sum(x['citation_count'] for x in rows if x['citation_correct'])/max(1,sum(x['citation_count'] for x in rows)),'no_evidence_accuracy':statistics.mean(x['no_evidence_correct'] for x in empty),'mean_latency_ms':statistics.mean(x['latency_ms'] for x in rows),'rows':rows}
  path=ROOT/'experiments/results/phase04';path.mkdir(parents=True,exist_ok=True)
  (path/'retrieval_evaluation.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
  print(json.dumps({k:{f:v for f,v in r.items() if f!='rows'} for k,r in output.items()},indent=2))
 finally: store.close()
