# Future Tasks

## QA Student UI

Phases 1–5 of the student app React rebuild (`APP/STUDENT_APP_REDUX/`) are complete. The following QA work remains:

- [ ] **Manual QA** — walk the full student journey with a real `VITE_TEST_USER_TOKEN` against the live backend: load dashboard → view weak concepts → run diagnostic → answer questions → check test mode → verify missed questions tab populates
- [ ] **designqc** — run `openwolf designqc --url http://localhost:5173` for visual polish review; check spacing, typography, color contrast, responsive layout
- [ ] **Backend endpoint tests** — add pytest tests for `GET /api/study/missed` in `backend/tests/` covering: success response, domain filter, sort_by options, empty result, invalid token
- [ ] **Performance check** — measure `/study/recommendations` fetch latency, React Query cache hit rates, no N+1 queries on backend
