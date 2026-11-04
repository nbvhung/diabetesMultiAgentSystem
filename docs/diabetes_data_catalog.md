# Versioned diabetes knowledge corpus 2.0

The research expansion uses **14 real NIDDK diabetes pages**. The source registry is `experiments/configs/diabetes_sources.json`. The prepared local corpus contains 449 normalized paragraph/list chunks in the current release; the manifest, not this prose, is authoritative after preparation. No generated medical evidence, patient profile or fabricated date is ingested.

| Source ID | Topic |
|---|---|
| definition | Diabetes definition and types |
| symptoms | Symptoms and causes, preserving diabetes type/section context |
| risk | Type 2 risk factors |
| prevention | Type 2 prevention/delay |
| tests | Educational descriptions of diabetes tests |
| living | Nutrition, physical activity and healthy living |
| management | Monitoring and diabetes management education |
| type1 | Type 1 definition/causes/education |
| type2 | Type 2 definition/causes/education |
| prediabetes | Insulin resistance and prediabetes |
| gestational | Diabetes during pregnancy |
| neuropathy | Diabetes-related nerve damage |
| foot | Diabetes and foot problems |
| eye | Diabetic eye disease |

All URLs are exact registered HTTPS paths; requests reject redirects, off-host URLs, query parameters and unknown source paths. `article.dk-content` text is parsed, preserving whole paragraphs and grouped lists. Small symptom/risk bullets are not discarded individually. Parent section context is retained so a type-specific or DKA passage is not silently treated as general diabetes evidence. References, trial recruitment, navigation, images/logos, third-party content and numeric medication-dose instructions are excluded. This is bounded public education coverage, not a comprehensive clinical guideline collection.

Source snapshots have actual retrieval UTC time, HTML SHA256, canonical URL, title and last-reviewed text only when present on the source. Unknown publication/review dates remain unknown. Source `last_reviewed` and `retrieved_at` have different meanings. Corpus/chunk IDs are content-addressed. `snapshots/<sha256>.html`, immutable chunk files and `releases/<corpus_sha256>.json` retain prepared-release provenance. Runtime verifies checksums before admission and never fetches content.

NIDDK's cached copyright policy is checked and recorded; it states most information is copyright free with exceptions. This implementation admits reviewed text only, excludes site logos/images and does not infer a blanket license for every linked article/graphic or other publishers. Raw snapshots/generated local corpus are gitignored. Policy: [NIDDK copyright](https://www.niddk.nih.gov/copyright).

## Graph

New labels `DiabetesSource`, `DiabetesEvidence`, `DiabetesTopic`, `DiabetesConcept`, `DiabetesAssertion` are separate from the historical Phase 04 graph. Queries select the exact active corpus release; archived development-release nodes are not counted as active knowledge. Seeding is idempotent.

Typed educational relations include HAS_RISK_FACTOR, HAS_SYMPTOM, SCREENED_WITH and HAS_COMPLICATION, with a supporting chunk, source URL, release and curated extraction-rule ID. Current release has 11 supported assertions; these are designated-source/phrase rules reviewed in code, not causal relationships inferred from Pima data or invented by an LLM. `GET /api/v2/knowledge/graph` exposes the exact supporting passages. Topic-to-source routing and paragraph reranking remain the main retrieval path; no scalable medical ontology/reasoner claim is made.

Graph assertion admission requires a designated source, an exact section and a reviewed supporting clause, recorded as `supporting_quote`, `section_context` and `curated-exact-source-clause-2.0`. A keyword such as “feet” in a footwear tip or “retinopathy” in a cataract paragraph is insufficient. Reseeding replaces the assertion's old support edge so only the admitted passage is exposed. API and regression tests check all eleven quotes and idempotent reseeding. The clauses are project-curated, not an expert-validated clinical ontology.

## Local models

- Sentence encoder: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384-dimensional embeddings, pinned local revision and checksums. Upstream pretrained, Apache-2.0.
- Cross encoder: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, query/passage relevance reranking on CPU, pinned revision/checksums. Upstream pretrained, Apache-2.0.

No LLM is trained in this expansion. Corpus vectors are computed from actual source chunks, with exact ID order, dimension, source release and encoder manifest hashes. A mismatching index is unavailable, never silently reused. Cross-encoder sigmoid values are ranking signals, not calibrated probabilities of clinical truth.

## Reproduce

```powershell
python -m pip install -e ".[dev,ml,knowledge,rl,semantic]"
python scripts/prepare_diabetes_corpus.py --fetch
python scripts/prepare_diabetes_embeddings.py --download
python scripts/prepare_diabetes_reranker.py --download
python scripts/seed_diabetes_graph.py
```

Model/source network downloads happen only in these explicit preparation commands. Subsequent serving is local/offline except configured Groq calls. If models are already cached, omit --download; to rebuild corpus from existing HTML omit --fetch. Do not rerun DL/RL training notebooks to prepare retrieval assets.

The API requires actual Neo4j. Its local corpus is a provenance store and embedding index, not an undisclosed fallback that pretends a failed Neo4j query succeeded. Missing graph → UNAVAILABLE/no evidence. Missing encoder/reranker → explicitly labeled retrieval fallback. The interface/source catalog and trace expose these states.

Model cards: [sentence encoder](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2), [cross encoder](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1). These upstream training datasets are distinct from this project's research/synthetic evaluation questions.
