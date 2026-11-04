# Phase 04 RAG within MAS

```mermaid
sequenceDiagram
    participant U as Question
    participant C as Coordinator
    participant K as Knowledge Agent
    participant R as Hybrid Retrieval
    participant N as Neo4j
    participant E as Education Agent
    participant S as Safety
    U->>C: POST /api/v1/mas/runs
    C->>K: typed KnowledgeTask
    K->>R: search(question, k=5)
    R->>R: controlled entity/keyword extraction
    R->>N: fixed parameterized read query, vector candidates
    R->>N: supported-by graph traversal
    R->>R: cosine ranks + reciprocal rank fusion/dedup
    R-->>K: EvidenceItem list
    K-->>C: COMPLETED with provenance or UNAVAILABLE
    C->>E: only valid evidence
    E-->>C: deterministic excerpts + citations, or abstention
    C->>S: output gate
    C-->>U: WorkflowResponse evidence/trace/citations
```

No standalone chatbot. Default Phase 03 prediction/PostgreSQL path is preserved and extended with integrated Knowledge/Education. Historical explicit scaffold factories keep stub tests. No weights/training/RL changed. Existing KnowledgeOutput/EvidenceItem/WorkflowResponse contracts unchanged (runtime 2.1); NO_EVIDENCE is a search outcome, not a new lifecycle enum: COMPLETED + evidence=[], trace reason and warning NO_EVIDENCE. Neo4j exceptions map to UNAVAILABLE/NEO4J_UNAVAILABLE with no evidence. No fallback to language-model knowledge.

## Ingestion and embeddings

BeautifulSoup extracts reviewed overview cards only; whitespace normalized. Whole sentences become bounded <=1200-character chunks; very long new content triggers review. Medicine/drug/dose sentences excluded; source text is never rewritten as medical claims. Controlled section→topic label/aliases mapping, no LLM extraction. Provenance/version retained. HashingVectorizer 512-dimensional normalized unigram/bigram embeddings, alternate_sign=False, English stop words. Stateless local sparse lexical embedding, not a pretrained semantic encoder and no external API/key. Embeddings stored as Neo4j chunk properties; this MVP uses exact in-process cosine over up to 1000 fetched chunk vectors, not ANN/native vector index. This is compatible vector retrieval for the bounded corpus, not scalable semantic RAG.

## Strategies

Retriever Protocol exposes search(question,k). vector/graph/hybrid share Retrieval implementation. k 1..10. Controlled English/Vietnamese alias matching maps query to curated entity ids; unsupported keywords return NO_EVIDENCE without querying Neo4j (scope gate, not connectivity probe). Queries keep every user-derived value in parameters. Graph uses entity→SUPPORTED_BY→chunk traversal. Vector search ranks by cosine, threshold 0.08; graph ranking also uses cosine within graph candidates. Hybrid merges top 20 per strategy with RRF 1/(60+rank), dedups by content ID, returns top k. Query is expanded only with controlled entity names. No arbitrary Cypher generation and no source URL supplied by user is fetched.

Education uses exact retrieved sentence excerpts, IDs and source URLs as a deterministic template; no LLM, no latent knowledge claims. Missing evidence abstains. Prompt-like retrieved content is filtered with a conservative pattern guard; text is never executed or treated as system instructions. This is not a complete adversarial text detector, but no tool invocation/prompt hierarchy exists for documents to alter. Tests include synthetic injected instruction. Evidence is checked again before display; Coordinator still checks IDs and Safety final veto. Excerpts are not personalized medical advice.

## API and configuration

Main workflow POST /api/v1/mas/runs; GET run/trace uses PostgreSQL unchanged. Debug/evaluation only: GET /api/v1/knowledge/health, POST /api/v1/knowledge/search {question,strategy,k}, GET /api/v1/knowledge/graph/summary. Missing Neo4j returns 503 for debug; primary workflow marks Knowledge UNAVAILABLE and continues honest abstention. Main workflow still needs configured/migrated PostgreSQL. Read health before assuming availability.

```powershell
# Dedicated local graphs/DBs only; migration tests alter disposable PostgreSQL schemas.
$env:NEO4J_TEST_URI='bolt://127.0.0.1:17687'
$env:PHASE02_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_phase02_test'
$env:PHASE03_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost:5432/diabetes_phase03_test'
python scripts/check_phase04.py
python scripts/evaluate_knowledge.py
```

Set NEO4J_URI for direct scripts; check_phase04 copies TEST URI into normal env and selects dedicated PG DB. No secrets in logs/source. Seed report in docs/validation/phase04/ingestion.json; API workflow proof api_workflow.json; metrics experiments/results/phase04/retrieval_evaluation.json.

## Evaluation definition and limits

24 hand-authored questions in experiments/configs/knowledge_eval.json: 20 answerable by reviewed overview sections (including multistep, sources, bilingual), 4 ambiguous/out-of-scope negatives. Relevance labels explicitly identify source sections; all sentence IDs within section are relevant. They are small-course author labels, not external expert adjudication or a held-out clinical benchmark. Recall@5 = recovered relevant sentence IDs / all labeled relevant IDs; MRR@5 on answerable cases. Citation correctness checks exact returned ID/excerpt/URL against accessed corpus, not clinical entailment or answer completeness. No-evidence accuracy on 4 negatives. Latency perf_counter around retrieval, machine/cache dependent, not load-test P95. These easy negatives do not demonstrate robust rejection for every off-topic query containing 'diabetes'. Hybrid need not beat graph or vector. No metrics written before running.

Known limits: tiny English overview corpus, keyword/entity ambiguity, hashing collisions, general passages may not fully answer detailed questions, lexical gate false positives/negatives, synchronous retrieval blocks async route, retained historical chunks on content change, no background ingestion scheduling or RBAC in temporary local graph. Full clinical KB, semantic encoder, expert relevance review and production governance remain outside this phase's claims.
