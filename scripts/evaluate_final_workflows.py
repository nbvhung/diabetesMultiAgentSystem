"""Bounded end-to-end bilingual evaluation, distinct from historical first-pass LLM test."""
from phase07_common import *
import argparse,time,statistics
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.app.research.api import Services
from backend.app.research.llm import GroqService
from backend.app.research.config import ResearchSettings
from evaluate_diabetes_rag import questions

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    app=create_app();provider=GroqService(ResearchSettings() if args.live else ResearchSettings(groq_api_key=None))
    if args.live and not provider.configured:raise SystemExit('Live provider not configured; no invented result')
    svc=Services(app.state,llm=provider);app.state.research_services=svc;svc.warmup()
    cases=[q for q in questions(svc.corpus) if q['split']=='confirmatory_phrasing'][:6]
    rows=[]
    try:
        with TestClient(app) as client:
            for item in cases:
                start=time.perf_counter();response=client.post('/api/v2/mas/runs',json={'question':item['question'],'language':item['language']});response.raise_for_status();run=response.json()
                assert client.get('/api/v2/mas/runs/'+run['run_id']).json()==run
                ids={e['evidence_id'] for e in run['evidence']}
                rows.append({'question_id':item['id'],'question':item['question'],'language':item['language'],'run_id':run['run_id'],'generation_mode':run['generation_mode'],'status':run['status'],'relevant_evidence':int(bool(ids&set(item['relevant_ids']))),'llm_accepted':int(run['generation_mode']=='llm' and run['grounding']['verified']),'evidence_count':len(ids),'retrieval_rounds':run['retrieval_rounds'],'latency_ms':(time.perf_counter()-start)*1000,'warnings':run['warnings']})
    finally:app.state.knowledge_store.close();app.state.db_engine.dispose()
    summary=[]
    for language in ['vi','en']:
        group=[r for r in rows if r['language']==language]
        summary.append({'language':language,'questions':len(group),'relevant_evidence_rate':statistics.mean(r['relevant_evidence'] for r in group),'accepted_llm_coverage':statistics.mean(r['llm_accepted'] for r in group),'latency_ms':statistics.mean(r['latency_ms'] for r in group)})
    plot_bars('final_workflows',summary,'language',['relevant_evidence_rate','accepted_llm_coverage','latency_ms'],'Bounded actual bilingual workflows; automated verification, not clinical accuracy')
    save('final_workflows',summary,rows,'Six previously inspected confirmatory phrasings evaluated through the full current Coordinator with bounded retries, SQL persistence and readback. Engineering regression, not a blind clinical test or directly comparable to first-pass LLM-only evaluation.',datasets=['experiments/configs/diabetes_confirmatory_questions.json','data/knowledge/diabetes-v2/manifest.json'],config={'live':args.live,'max_questions':6,'max_provider_attempts_per_run':4,'maximum_provider_attempts_total':24,'selection':'first three topic families, vi/en each; previously inspected development cases','threshold_tuning':False})

if __name__=='__main__':main()
