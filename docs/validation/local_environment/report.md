# Local environment / real Groq integration verification

Update 2026-11-03: following a Windows reboot, neither Neo4j port was listening. The local instance was restarted; authenticated Bolt access, all 449 evidence chunks/14 sources/11 supported assertions and Browser HTTP 200 were verified again. Chromium loaded the actual Browser login page. [Recovery evidence](neo4j_restart_recovery.json), [Browser screenshot](neo4j-browser.png). Use the project-root `start_neo4j.cmd` after reboot; Windows auto-start has not been installed. Existing data and credentials were retained.

**LOCAL_ENVIRONMENT_VERIFIED**, UTC 2026-11-02T20:20:43.845046+00:00. This is a newer connection/integration smoke check, separate from the full offline regression snapshot in `../diabetes_expansion/` and from a model-quality benchmark. [Vietnamese .env / Neo4j instructions](../../local_environment_vi.md), [machine results](results.json).

Code: `source-sha256:4123ea737db80711cd0659173c428f7e502589dc441ac9f1eb9ebd992c924deb`. No Git repository was initialized. Frozen DL/RL files still match the original Phase 07 SHA256 map.

| Component | Actual check |
|---|---|
| PostgreSQL | Credentials from the user's .env connected; Alembic upgrade applied; migration `0002_phase03`; actual prediction/run/trace persisted and read back |
| Neo4j | Separate password-protected instance, Bolt 7687 / HTTP 7474, loopback only; valid credentials accepted and wrong password rejected |
| Graph | 449 current-release chunks, 14 NIDDK sources, 11 exact-clause-supported assertions; idempotent seeding and persistence after stop/start verified |
| Groq | Two smoke questions in separate executions, each with generation and independent review; four actual HTTP 200 responses, model `openai/gpt-oss-20b` |
| MAS API | POST v2 returned 201; all six agents COMPLETED, independent LLM proof, both Safety gates allowed; committed GET run/trace equal to original response |
| Adapter regression | 12 focused tests passed, 42 deselected; this is not a new full-suite pass claim |

The API smoke run is `8215e17d-a281-4228-a12b-207de0baa1da`. Its status is DEGRADED solely for `W03_RESEARCH_SCORE`, an intentional warning that the synthetic MLP score is research output. All dependencies and all six agent results were available/completed. [API probe](api_probe.json), [synthetic run/trace snapshot](e2e_run.json), [single-question provider probe](groq_probe.json), [SQL probe](postgresql_probe.json).

No real patient information was used. Only a fixed synthetic assessment and public-source educational question reached this workflow. The API adapter excludes assessment features from Groq prompts; secrets are not printed in these reports.

The initial real provider attempts returned `json_validate_failed`; safe metadata was retained in [before-fix probe](groq_probe_before_fix.json). GPT-OSS now explicitly uses `reasoning_effort=low`, `include_reasoning=false` while retaining strict schema, exact quote/number admission, separate semantic review and mandatory Safety. JSON failure has the sanitized `GROQ_STRUCTURED_OUTPUT_REJECTED` code. Both real smoke executions passed after the change. No rejected prose/reasoning was retained or released.

Neo4j's original launcher/configuration could not resolve the Unicode workspace path correctly. The configured instance uses `D:\diabetes-mas-local\neo4j` with the installed ASCII-path Neo4j 5.26 binaries and Java 17. Script `scripts/local_neo4j.py` manages setup/start/status/stop and matches a project-specific JVM ownership argument before stopping anything. The local instance is left running for the user; no Windows auto-start service was installed. User PostgreSQL services were not stopped.

These are connectivity and workflow results, **not accuracy metrics**: `quality_metrics=null`. Automated semantic approval is not clinical validation. The six-question/full LLM benchmark and human source review remain outstanding; there is no READY_FOR_PHASE_08 claim from two smoke examples. Historical experiment manifests retain the source hashes from their own actual executions rather than being relabeled for the new helper/adapter changes.
