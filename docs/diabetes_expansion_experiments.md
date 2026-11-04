# Grounded diabetes expansion — experimental protocol

No result is created from a placeholder LLM, fabricated evidence or invented metric. New artifacts use names `diabetes_rag`, `diabetes_mas`, `diabetes_safety`, optional `diabetes_llm`. Historical Phase 07 artifacts remain separate; their corpus/benchmark is different and their scores are not a valid before/after comparison to this expansion.

## Knowledge and retrieval

`diabetes_benchmark.json` contains 20 manually authored question families with four Vietnamese/English phrasings per family. Manual target source IDs + section substrings expand to exact source-version chunk IDs before execution. They are coarse retrieval-target labels, not a clinical semantic-answer gold standard; another medically valid passage in a different section may be a false negative. Five unanswerable/out-of-scope questions are scored separately.

The first 80 questions were used for development and diagnosis, including inspecting the initial bi-encoder aggregate. They are not described as blind test data after those inspections. A separate `diabetes_confirmatory_questions.json` fixes 40 additional phrasings after the cross-encoder architecture/thresholds were selected. Sources/topics overlap; this is a confirmatory wording check, not external clinical validation or a large unbiased scientific trial. No hyperparameter change is justified by its final score in this implementation.

All 125 questions use the same 14-source corpus release for lexical, semantic, graph and hybrid retrieval. Maximum three returned passages; no forced padding with irrelevant evidence; max two per source. Hybrid uses graph constraints plus dense/lexical candidate pooling and the actual multilingual cross encoder over up to 16 pairs. Thresholds and model revisions/checksums are recorded in manifests. This is a retrieval/reranking ablation; hybrid's additional reranker computation is part of that method and is not concealed.

Metrics: Recall@3, MRR@3, mean precision among returned passages (zero for an answerable query with no result), exact citation provenance, no-evidence accuracy and latency. No-evidence outcomes are not counted as a correct citation. Ranker scores are not calibrated clinical probabilities. Report development, diagnostic and confirmatory splits separately. English/Vietnamese rows are retained for audit.

```powershell
python scripts/evaluate_diabetes_rag.py
```

## MAS comparison

The same-tool direct baseline calls the same retriever, policy, compose/verify functions and deterministic Safety gates without Coordinator, registry messages or agent execute. MAS uses six typed agents, bounded retrieval feedback and draft-repair control. Both have the same model/evidence access; neither receives fake business outputs. Evaluation order is seeded/shuffled, model assets warmed before timing, connection/reflection/rollback excluded equally.

The offline benchmark explicitly disables the provider in both methods. It measures actual orchestration/source-evidence/fallback behavior, not generated LLM quality. Selected diagnostic questions plus unanswerable/adversarial cases run twice per method. Ground truth requires relevant evidence availability or expected refusal, and both Safety gates. Report task completion, evidence relevance/provenance, software safety invariants, retrieval rounds, latency and actual LLM-generated run count. The latter is zero when disabled, with no inferred LLM-quality score. No MAS superiority claim is made from identical outcomes or untested clinical hypotheses.

```powershell
python scripts/evaluate_diabetes_mas.py
```

The held-out DL prediction and simulator RL comparisons from earlier phases remain applicable to the unchanged artifacts. The checker verifies their SHA256 files stay frozen. New API integration still exercises actual prediction persistence and RL policy/fallback; this expansion did not retrain them or invent a new neural training result.

## Safety and software faults

Actual v2 API scenarios test safe diabetes questions, medication dosing, diagnosis requests and prompt injection. Explicit synthetic agent faults test timeout and a quote altered while keeping a real source ID/URL. Separate rule probes verify that public-education conditionals are distinguished from personal categorical diagnoses. Missing model/graph/policy/key, provider errors/truncation, fake quote/numbers, proof/candidate mismatch, compromised verifier approval, concurrent persistence and old-snapshot compatibility are also regression-tested.

Fault-injected or mocked-provider software tests are labeled and are not real LLM answer-quality results. A forged-quote conflict probe establishes provenance rejection; it does not establish reasoning over two authentic but medically conflicting guidelines. Controlled clarification and exact-source fallback are different from LLM-generated answers. Benchmark failures are retained, not silently relabeled.

```powershell
python scripts/evaluate_diabetes_safety.py
```

### Retained development failure

The first full expansion check failed on the existing safe question `What lifestyle and physical activity topics are described?`: it returned controlled clarification without evidence, although relevant activity passages existed. Expected behavior was kept unchanged. Diagnostics established that the retry still ranked the unchanged question; keyword appending did not recover evidence. The fix uses deterministic natural-language topic reformulation for the second attempt's dense retrieval and reranking, while retaining the original question for generation/review. An actual API regression requires recovery with evidence in two attempts. Original failed safety rows, manifest and checker result are retained in `validation/diabetes_expansion/before_retry_fix/`.

This fix is based on that development safety case. The first-pass retrieval/reranker behavior and thresholds used by the 40 confirmatory phrasing measurements are unchanged; those measurements do not evaluate retry behavior. All final results are descriptive software/retrieval results; no clinical or blind external validation is claimed.

## Live LLM gate

```powershell
python scripts/evaluate_diabetes_llm.py --live --limit 6
```

This uses actual Groq calls and reports model ID, generation mode, measured tokens/latency, separate verifier acceptance and approved response/source IDs for later human review. The verifier shares the provider but uses its own role/call; its judgments are fallible. Its acceptance rate is not medical accuracy. Rejected prose is not exported. Rate/auth/timeout failures are recorded with sanitized codes.

Without key or --live, write NOT_RUN with `quality_metrics=null` and zero remote requests. With no actual generated response, create no model-quality figure or measured bundle. UI therefore shows unavailable for that experiment. A full conversational-readiness claim remains blocked until actual provider and human-grounding evaluation; the offline checker can only report implemented/pending live validation.

### KG admission audit

A manual inspection of all eleven initial assertion passages found that permissive keyword matching could select a foot-warming tip for a complication edge, or a cataract paragraph for retinopathy. This was corrected before final delivery: every assertion now requires an exact reviewed source clause in its designated section, and graph seeding replaces superseded support edges. Regression checks include unrelated eye/foot paragraphs and two actual graph ingestions with exactly one admitted support per assertion. These are provenance/curation checks, not clinical expert validation.

## Artifacts and reproduction

`scripts/check_diabetes_expansion.py` captures all commands/return codes, checks historical and new tests without skips, verifies model/policy hashes, seeds actual Neo4j, runs measurements/demos/browser checks, and writes machine status. Actual report/screenshots: `docs/validation/diabetes_expansion/`.

Each measured bundle includes summary/rows CSV, JSON, PNG and timestamp/code hash/config/dataset hash/seed/environment/output hash manifest. Existing experiment API verifies integrity before serving. Missing/incomplete/tampered outputs are unavailable. There is no fake Git commit: this workspace has no initialized repository, so code provenance uses a full source-file SHA256 map. Local manifest integrity is not an attacker-resistant signature.
