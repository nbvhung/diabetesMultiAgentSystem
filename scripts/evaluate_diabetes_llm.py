"""Bounded live Groq composition + independent review; never fabricates model metrics."""
from phase07_common import *
import argparse,asyncio,time,statistics
from backend.app.research.config import ResearchSettings
from backend.app.research.llm import GroqService
from backend.app.research.corpus import Corpus
from backend.app.research.graph import DiabetesGraph
from backend.app.research.retrieval import Retriever
from backend.app.research.grounding import compose,verify_candidate
from evaluate_diabetes_rag import questions


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--limit',type=int,default=6,choices=range(1,13));args=parser.parse_args()
    provider=GroqService(ResearchSettings());log=ROOT/'docs/validation/diabetes_expansion';log.mkdir(parents=True,exist_ok=True)
    if not args.live or not provider.configured:
        status={'status':'NOT_RUN','reason':'GROQ_API_KEY_NOT_CONFIGURED' if not provider.configured else 'RUN_WITH_LIVE_FLAG','timestamp':datetime.now(timezone.utc).isoformat(),'provider':provider.status(),'live_requests':0,'quality_metrics':None,'code_version':source_version()[0]}
        (log/'llm_live_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8');print(json.dumps(status,indent=2));return
    corpus=Corpus();corpus.load();graph=DiabetesGraph();retriever=Retriever(graph,corpus);rows=[]
    try:
        for item in [q for q in questions(corpus) if q['split']=='confirmatory_phrasing'][:args.limit]:
            result=retriever.search(item['question']);started=time.perf_counter()
            candidate=await compose(item['question'],item['language'],result.evidence,None,provider)
            proof=await verify_candidate(candidate,result.evidence,corpus,provider,item['question'])
            # Rejected text is not written to artifacts. Only independently approved
            # text and source IDs may be included for later human review.
            rows.append({'question_id':item['id'],'language':item['language'],'generation_mode':candidate.generation_mode,'accepted':int(candidate.generation_mode=='llm' and proof.verified),'claims':len(candidate.claims),'verification_mode':proof.mode,'reason_codes':proof.reason_codes,'provider_error':candidate.provider_error,'latency_ms':(time.perf_counter()-started)*1000,'input_tokens':candidate.input_tokens+proof.input_tokens,'output_tokens':candidate.output_tokens+proof.output_tokens,'approved_response':candidate.text if candidate.generation_mode=='llm' and proof.verified else None})
    finally:graph.store.close()
    actual=[r for r in rows if r['generation_mode']=='llm']
    status={'status':'LIVE_EXECUTED' if actual else 'LIVE_ATTEMPT_FAILED','timestamp':datetime.now(timezone.utc).isoformat(),'actual_generated_responses':len(actual),'attempted_questions':len(rows),'provider':provider.status()}
    (log/'llm_live_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    if not actual:
        (log/'llm_live_failures.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        raise SystemExit('No genuine LLM response; no quality metric or figure created')
    summary=[{'provider':'Groq','model':provider.config.groq_model,'questions':len(rows),'actual_llm_responses':len(actual),'independent_verifier_acceptance':statistics.mean(r['accepted'] for r in actual),'latency_ms':statistics.mean(r['latency_ms'] for r in actual),'input_tokens':sum(r['input_tokens'] for r in rows),'output_tokens':sum(r['output_tokens'] for r in rows)}]
    plot_bars('diabetes_llm',summary,'provider',['independent_verifier_acceptance','latency_ms'],'Actual Groq responses / automated verifier acceptance; not human clinical accuracy')
    save('diabetes_llm',summary,rows,'Actual remote LLM calls. Automated verifier acceptance is not clinical accuracy; approved responses require further human source review.',datasets=['experiments/configs/diabetes_benchmark.json','data/knowledge/diabetes-v2/manifest.json'],config={'model':provider.config.groq_model,'limit':args.limit,'temperature':0,'output_token_limit':provider.config.groq_max_output_tokens,'generation':'source-only JSON claims','verifier':'separate prompt/call; deterministic source quote/number validation first'})

if __name__=='__main__':asyncio.run(main())
