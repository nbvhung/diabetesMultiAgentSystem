# Current diabetes graph — runtime 3.0 / Phase 08

The active graph uses 14 registered NIDDK pages, 449 admitted chunks and 11 source-supported assertions. Native seed/load and HTTPS workflow retrieval have been verified. Current labels are DiabetesSource, DiabetesEvidence, DiabetesTopic, DiabetesConcept and DiabetesAssertion; relationships include HAS_CHUNK, SUPPORTED_BY, SUBJECT_OF, OBJECT and allowlisted domain predicates. The source-of-truth implementation is `backend/app/research/graph.py`; [schema figure](report/figures/neo4j_schema.png), [data catalog](diabetes_data_catalog.md), [RAG/LLM design](llm_grounding.md).

Each chunk binds an exact URL, source SHA256, release, section, excerpt and retrieval timestamp. An assertion is admitted only if its reviewed supporting clause occurs in the designated source section. Clinical causality is not inferred from Pima correlations. Ingest uses constraints/MERGE and replaces generated support edges idempotently; old release history is not relabeled. Retrieval reads the active corpus release. No source is invented when graph access fails.

Embeddings/reranker run locally on CPU with offline-only loaders; they are not patient data or a locally trained LLM. Sources are public educational pages, not ADA/WHO guidelines silently added to the corpus. Native seed was repeated by tests; Docker volume persistence has not been verified. The original small graph below is retained as **historical Phase 04**, not the current 449-chunk release.

# Historical Phase 04 Neo4j knowledge graph

Only NIDDK Diabetes Overview text is currently ingested: https://www.niddk.nih.gov/health-information/diabetes/overview . Usage policy accessed separately: https://www.niddk.nih.gov/copyright . Policy says majority of site information is copyright free; this corpus excludes logos/images/third-party materials and medicine/dose sentences. This is not a blanket license for every NIH/ADA/WHO document. CDC, ADA Standards and WHO are not ingested or represented as sources. No generated citations or Pima correlations enter the graph.

## Ontology and provenance

| Label | Meaning |
|---|---|
| Condition | Diabetes, gestational and other types overview topics |
| RiskFactor | Risk-factor topic, not an inferred causal factor |
| Symptom | Symptom topic supported by source sentences |
| DiagnosticTest | Tests/diagnosis educational topic; not a diagnostic service |
| LifestyleTopic | Meal/activity education topic |
| EducationalAction | Prevention and care-team topics |
| Guideline | Patient-education overview container (kind explicitly says this); NOT ADA Standards or formal clinical guideline |
| Source | Accessed NIDDK overview, provenance and version |
| DocumentChunk | Exact normalized source sentence with embedding and metadata |

Implemented edges: Source HAS_CHUNK DocumentChunk; topic SUPPORTED_BY chunk; Diabetes RELATED_TO topic; education Guideline REFERENCES Source. Stronger HAS_RISK_FACTOR/HAS_SYMPTOM/USES_TEST/RECOMMENDS_EDUCATION are reserved vocabulary, not fabricated edges. No inferred causality. One-hop supported-evidence traversal is actual graph retrieval.

Unique id constraints for all nine labels; chunk.section index. Topic ids are curated; Source id is exact canonical URL; chunk id SHA256(URL|section|sentence). Repeated ingestion MERGEs same IDs/edges. Ingestion report verifies equal counts after two runs. Content change creates new content-addressed chunks; historical chunks currently retained and may be retrieved. This version does not implement source-version retirement, so re-fetch after publisher edits requires review before production use.

Source/chunk metadata: title, publisher, canonical URL, retrieved_at (UTC; cached initial download uses file modification time if no sidecar), publication_date=null when unknown, section, version=content digest, usage_notes with policy URL. No fabricated update date. Full metadata retained in Neo4j and ingestion report; EvidenceItem keeps existing v1 schema subset (id/title/url/publisher/section/retrieved_at/excerpt). Evidence IDs map back to DocumentChunk. No schema migration needed for EvidenceItem.

## Scope and limits

The initial corpus is deliberately small: nine overview topics and sentence chunks. It names type 1/type 2/gestational diabetes, general risk factors/symptoms/tests, lifestyle/prevention and speaking with care team. It does NOT contain detailed diagnostic thresholds, all test names, full type-specific etiology, medication instructions or comprehensive recommendations. A retrieved general passage may not answer a detailed question; no broad clinical coverage claim. English source text; bilingual keyword aliases limited to a few Vietnamese phrases.

## Running locally

Install `python -m pip install -e ".[dev,ml,knowledge]"`. Configure NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD through environment or .env; do not commit secrets. Use a dedicated graph for seeding/evaluation. Run:

```powershell
python scripts/seed_knowledge.py --fetch
python scripts/seed_knowledge.py
```

--fetch accesses only allowlisted HTTPS NIDDK URLs and validates final URL, stores raw HTML under data/knowledge (gitignored); loader refuses absent files or unrecognized layout/usage policy. No silent offline fabricated source. Cached seed uses the actual downloaded HTML. Raw source/version and normalized excerpts available for audit. Data origin is real public educational material, not synthetic medical evidence.

Actual verification uses Neo4j Community 5.26 portable, Java 17, isolated D:/TEMP/diabetes-neo4j-phase04, Bolt 127.0.0.1:17687, HTTP 127.0.0.1:17474. Auth disabled ONLY for this temporary loopback test graph; use authentication/read-only service credentials in normal operation. No external existing graph modified. Windows Unicode paths failed classpath resolution, so portable runtime copied into ASCII temporary path; code/notebooks remain in repository.

Constraints/index and import require write privileges; API only uses fixed SELECT-like Cypher via read sessions. Community read-session routing alone is not an authorization boundary; deploy read-only credentials where supported. No user question is compiled into Cypher.
