# Verification - 2026-11-06

- Backend: 216 passed, 43 skipped, one dependency deprecation warning. Dedicated integration DB environment variables were not configured. Existing migration tests can downgrade schemas; the application DB was not substituted.
- Frontend: npm test: 22 passed. TypeScript/Vite build passed.
- python scripts/check_report_v2.py --live: PASS. Exact exported DML imported twice on real Neo4j; idempotence, full evidence/assertion property readback and edge counts passed. Transaction rolled back. See kb_checks.json for hashes and details.
- Neo4j was initially stopped; started successfully before the passing live check. The initial connection failure is not counted as a pass.
- Historical scientific metrics were not remeasured. No clinical validation claim.
- Actual Chrome browser check: **PASS**, 11 assertions, symptom filter returns 3, passage expansion works, mobile width 390 has no horizontal overflow, zero page errors. See `browser.json`, `kb-desktop.png`, `kb-mobile.png`. Reproduce: `node frontend/check-kb-v2.mjs` with the native demo running.
