# Future Features & Outstanding Work

Consolidated from `future_tasks.md` and `_deprecated/rules_v*/future_plans.md`.

---

## QA — Student App

Phases 1–5 of `APP/STUDENT_APP_REDUX/` are complete. Remaining QA:

- [ ] **Manual QA** — walk the full student journey with a real `VITE_TEST_USER_TOKEN` against the live backend: load dashboard → view weak concepts → run diagnostic → answer questions → check test mode → verify missed questions tab populates
- [ ] **designqc** — run `openwolf designqc --url http://localhost:5173` for visual polish review; check spacing, typography, color contrast, responsive layout
- [ ] **Backend endpoint tests** — add pytest tests for `GET /api/study/missed` covering: success response, domain filter, sort_by options, empty result, invalid token
- [ ] **Performance check** — measure `/study/recommendations` fetch latency, React Query cache hit rates, no N+1 queries on backend

---

## Admin Dashboard — Remaining Work

`APP/ADMIN_APP/` Phase 2 (frontend) is scaffolded. Remaining:

- [ ] **QA Admin UI** — run against live backend with a real admin token; verify all 4 pages load, filters work, approve/reject mutations persist
- [ ] **Auth guard** — add admin token validation and redirect to login if token is missing or invalid
- [ ] **designqc** — run `openwolf designqc --url http://localhost:5174` for visual polish
- [ ] **Student Performance deep-dive** — add cohort view: accuracy across all students per focus key, which questions have the highest miss rates system-wide
- [ ] **Data Management — question detail page** — click into a single question to view full annotation, version history, audit log, and edit form
- [ ] **Backend endpoint tests** — pytest tests for admin question approve/reject/edit endpoints

---

## Generation Pipeline — Batch Scheduler

Not yet built. Currently generation is triggered manually.

- [ ] **Production batch scheduler** — automatically maintains the 100-question blueprint, produces generation batches by domain/difficulty target, respects rotation rules (no repeated `topic_broad` consecutively, no repeated `topic_fine` within a 5-item window)
- [ ] **Stats-driven module requests** — scheduler auto-emits module generation requests when updated `practice_exam_stats` snapshot is available, using real distribution data to drive domain and difficulty targeting
- [ ] **Adaptive second module generation** — automated generation of `sec01_mod02` higher/lower route with correct difficulty ramp (`clustered_progressive` for higher, `gentle_progressive` for lower), triggered by student module 1 performance score

---

## Generation Pipeline — Validation & Repair

Validator passes 1–6 exist. Pass 7 and automated repair loop are missing.

- [ ] **Pass 7: Set-level distribution validator** — checks full 27-question module for answer-position streaks (max 3 same answer in a row), domain coverage balance, difficulty ramp compliance, question-family repetition limits
- [ ] **Automated repair loop** — structured re-prompting of failed validator items: report failures as structured JSON, re-generate with failure context injected into prompt, re-validate, max 3 repair attempts before flagging for manual review
- [ ] **Second-model review pass** — dedicated SAT realism review on accepted items using a separate model (e.g. GPT-4o or Claude Opus) before export to production question bank; checks: realistic SAT style, distractor plausibility, passage authenticity

---

## Generation Pipeline — Module Blueprints

- [ ] **Module blueprint registry** — store `sec01_mod01`, `sec01_mod02_higher`, `sec01_mod02_lower` blueprints as versioned config; allow overrides per course, diagnostic set, or remediation target
- [ ] **Blueprint-driven generation UI** — admin page to select a blueprint, override domain/difficulty quotas, and trigger a generation run with live progress tracking

---

## Student App — Future Enhancements

Ideas not in current scope but worth tracking:

- [ ] **Spaced repetition** — resurface missed questions using SM-2 or similar algorithm instead of fixed resurface window
- [ ] **Progress over time** — chart student accuracy trend by week/month per domain
- [ ] **Full test simulation** — two-module adaptive test (mod01 → mod02 higher/lower based on mod01 score), with score estimate at the end
- [ ] **Passage-based questions** — student UI support for displaying passages alongside questions (currently grammar-only)
