# UI/UX redesign and project review — actual verification

**UIUX_DELIVERED_RESEARCH_REVIEWED**. Verified UTC 2026-11-03T06:21:07.528308+00:00; code `source-sha256:141fe64ad44912b0739c5e8615ebda900bf5e5935ee0f738f8a9c75bb70bd518`. Scope: user-requested frontend redesign and review of existing training/evaluation artifacts before Phase 08. No training, serving threshold, weights, policy or backend route change. [Project/training review](../../project_review_uiux.md), [machine results](results.json).

The UI now uses Vietnamese primary navigation, clearer entry points, topic shortcuts and a local SVG agent illustration; no image generator, new UI dependency or fabricated personal/clinical dashboard data. Question answers use numbered actual citations and expandable source passages. Technical trace is on its own page with a decision filter. Research cards only use verified API report values; absent results stay absent. Synthetic confirmation, research-score limitations, Safety and explicit LLM/extractive/clarification/withheld modes remain visible.

Responsive navigation, larger reading text, visible input labels/focus, a skip link and reduced-motion CSS improve accessibility; this is not a full WCAG conformance certification. Navigation resets scroll; successful requests bring the result into view. Waiting shows real elapsed time, with no fake agent progress or fabricated completion percentage.

| Executed check | Result | Evidence |
|---|---|---|
| Frontend `npm test` (same Vitest CLI) | 22 passed, no failed/skipped tests | [unit log](frontend_unit.log) |
| `npm run build` | TypeScript and Vite exit 0 | [build log](frontend_build.log) |
| Playwright actual browser/API suite | 6 passed; zero skipped/flaky/retries | [browser log](browser.log), [JSON](browser-results.json) |
| One actual live UI question to existing API/Groq | HTTP 201, LLM generation, independent verifier, 2 published citations, zero page errors | [live run](live-run.json), [answer screenshot](live-answer.png) |
| Frozen model/policy SHA256 | All original files equal to Phase 07 | [machine results](results.json) |
| Existing measured report integrity | prediction/RL/diabetes RAG/MAS/safety bundles verified | Source CSV and manifests retained unchanged |

Browser scenarios cover real synthetic assessment → six completed agents → actual citations → PostgreSQL readback/trace, unsafe medication veto, isolated actual graph outage/no citations, measured figures and category filter, 390px mobile navigation/topic shortcut/no horizontal overflow, and weak-evidence bounded retrieval/clarification. The QA APIs used ports 18000/18001 with the provider explicitly disabled to avoid remote quota consumption in the regression suite; these are real FastAPI/SQL/Neo4j/model/policy/rule paths, not canned JSON. The separate live screenshot used the existing user API and actual Groq.

The first browser run found a new monitor rendering error for JSON `duration_ms=null`. The frontend type and formatting guard were corrected and a regression test added; the final six browser scenarios pass. There is no claim of a freshly rerun full backend suite from these frontend checks. No artificial accuracy or LLM quality metric was created from the single live example.

## Screenshots

[Overview](overview.png), [knowledge composer](knowledge.png), [real Groq answer](live-answer.png), [synthetic assessment](assessment.png), [agent monitor](monitor.png), [experiments](experiments.png), [mobile overview](mobile.png), [mobile question](mobile-question.png), [Safety veto](unsafe.png), [graph unavailable](knowledge-unavailable.png), [clarification](clarification.png). Overview, live answer and mobile captures were visually inspected. All are real browser screenshots.

## Research conclusions

MLP accuracy 0.758621 / recall 0.536585 / F1 0.611111; LR accuracy 0.775862 / F1 0.617647. Checkpoint epoch 24 was selected from 44 training epochs by validation loss; 19/41 positive test labels are missed at threshold 0.5. Q-learning reward 4.276/completion 0.97 versus rule-based 4.311/0.983333: no RL superiority shown. Hybrid confirmatory MRR@3 0.625 and returned-passage precision 0.570833 improve over other methods on those measures, but semantic recall is higher. Offline MAS completion 0.863636 versus direct workflow 0.727273 uses different retry budgets; it is not a causal proof of agent decomposition or LLM answer quality. Full caveats, data sources and prioritized next work are in the linked project review.

The user's existing backend 8000 and Vite 5173 were retained. Only the two owned QA API children were stopped. Live app URL remains `http://127.0.0.1:5173`; reload the browser to see the new UI. Phase 08 remains unimplemented; source-grounded benchmark design, matched-budget MAS evaluation, DL CV/calibration and RL simulator/override analysis remain research work, not completed claims.
