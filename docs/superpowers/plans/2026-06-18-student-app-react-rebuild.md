# Student App React Rebuild — Implementation Plan

> **For agentic workers:** Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Crash-recovery note:** This plan was recovered from a crashed session on 2026-06-18. Decisions are checkpointed in Claude memory at `project_student-app-react-rebuild.md`. Update that memory after each chunk completes.

**Goal:** Transform the student-facing app from a 2-page prototype (`PracticePage`, `StatsPage`) into a full multi-page DSAT prep suite — diagnostics, dashboard, test mode, practice, statistics, missed questions, weak concepts — by **extending** the existing `FRONTEND/` React stack and porting the standalone `grammar-app.html` into a React component. No framework switch.

**Architecture:** Stateless React SPA consuming REST APIs from the existing DSAT FastAPI backend. React Query for server state, React Router v7 for routing, Tailwind + Radix UI for UI, Framer Motion for animations. The `grammar-app.html` vanilla JS becomes a custom hook + component pair; all 11 function signatures are preserved so the backend contract is unchanged. New backend endpoints extend `student.py` only where the existing `/questions`, `/submit`, `/stats/{user_id}`, `/study/*` surface is insufficient.

**Tech Stack:**
- Frontend: React 18 + TypeScript + Vite + React Router v7 + @tanstack/react-query + Tailwind + Radix UI + Framer Motion (existing + 1 new dep)
- Backend: FastAPI (existing `backend/app/routers/student.py`)
- Database: PostgreSQL (existing schema — Question, QuestionOption, QuestionAnnotation, User, UserAnswer)
- Testing: pytest (backend), Vitest + React Testing Library (frontend, new)

---

## Current State (verified 2026-06-18)

**Backend `student.py` endpoints already present:**
- `GET /questions` — filtered question fetch (domain, difficulty, limit, user_token for exclude_seen)
- `POST /submit` — answer submission + correctness
- `GET /stats/{user_id}` — user accuracy stats
- `POST /study/recommendations` — weak-concept recommendations
- `POST /study/generation-requests` — generate study material batch
- `GET /study/generation-requests/{batch_id}` — batch status

**Frontend `FRONTEND/` already present:**
- Routes: `/` (PracticePage), `/stats` (StatsPage) via `BrowserRouter`
- API client: `fetchQuestions`, `submitAnswer`, `fetchStats`, `fetchFilterInventory`
- Stack wired: `QueryClientProvider`, React Query, Tailwind, Radix UI primitives (`button`, `radio-group`, `badge`)
- Components: `QuestionCard`, `SessionSetup`, `SessionComplete`, `StatsPanel`, `TestTimer`

**`grammar-app.html`** — standalone SPA, 11 functions (renderSentence, renderOptions, renderGrammarKeys, renderTrapSummary, renderExplanations, selectAnswer, renderFeedback, toggleKey, clearKeys, findTraps, + getKey/findActiveKey helpers) + data blocks (GRAMMAR_KEYS, TRAP_ANALYSIS, TOKENS, OPTIONS). Currently hardcoded single question.

---

## File Structure

**Frontend new/modified:**
- `FRONTEND/src/main.tsx` — MODIFY: add new routes
- `FRONTEND/src/App.tsx` — MODIFY: nav + routes for 5-6 new pages
- `FRONTEND/src/hooks/useGrammarSession.ts` — CREATE: the 11 functions as a custom hook
- `FRONTEND/src/components/GrammarPractice.tsx` — CREATE: React render of the grammar app
- `FRONTEND/src/api/study.ts` — CREATE: /study/* client functions
- `FRONTEND/src/api/diagnostic.ts` — CREATE: diagnostic endpoints client
- `FRONTEND/src/pages/DashboardPage.tsx` — CREATE
- `FRONTEND/src/pages/DiagnosticPage.tsx` — CREATE
- `FRONTEND/src/pages/TestModePage.tsx` — CREATE
- `FRONTEND/src/pages/WeakConceptsPage.tsx` — CREATE
- `FRONTEND/src/pages/MissedQuestionsPage.tsx` — CREATE
- `FRONTEND/src/types/index.ts` — MODIFY: add diagnostic/study/missed-question types
- `FRONTEND/package.json` — MODIFY: add framer-motion

**Backend new/modified:**
- `backend/app/routers/student.py` — MODIFY: add missed-questions + diagnostic endpoints
- `backend/app/models/payload.py` — MODIFY: add response models as needed
- `backend/tests/test_student_router.py` — MODIFY: new endpoint tests

---

## Chunk 1 — Port grammar-app.html → React (no new pages yet)

**Objective:** Render the grammar app inside the React tree at `/practice/grammar`, preserving all 11 function signatures. Data still hardcoded in this chunk; API wiring is Chunk 3.

### Task 1.1: Extract data blocks to a typed module
- [ ] **Step 1:** Create `FRONTEND/src/data/grammarKeys.ts` exporting `GRAMMAR_KEYS`, `TRAP_ANALYSIS`, `TOKENS`, `OPTIONS` as typed consts (copy verbatim from `grammar-app.html`).
- [ ] **Step 2:** Add matching types to `FRONTEND/src/types/index.ts` (`GrammarKey`, `TrapAnalysis`, `Token`, `GrammarOption`).

### Task 1.2: Build the `useGrammarSession` hook
- [ ] **Step 1:** Create `FRONTEND/src/hooks/useGrammarSession.ts`. Move the 11 functions into the hook, returning `{ render state, actions }` instead of mutating DOM directly. State: `selectedAnswer`, `activeKeys`, `revealed`, `feedback`.
- [ ] **Step 2:** Preserve function names as hook-returned callbacks: `selectAnswer`, `toggleKey`, `clearKeys`, `findTraps`, `getKey`, `findActiveKey`. Keep signatures identical for backend-compat.
- [ ] **Step 3:** The render* functions become derived state (useMemo) or JSX-returning helpers inside the component, not DOM writes.

### Task 1.3: Build `GrammarPractice` component
- [ ] **Step 1:** Create `FRONTEND/src/components/GrammarPractice.tsx` consuming `useGrammarSession`. Render sentence (with token highlighting), options (A–D radio), grammar-key buttons, trap summary, explanation cards, feedback.
- [ ] **Step 2:** Port the CSS from `grammar-app.html` `<style>` into Tailwind classes + a small `GrammarPractice.css` if needed. Match the modernized palette (variables: `--color-primary` #667eea etc.).
- [ ] **Step 3:** Add Framer Motion for option/key transitions (the "animations" requirement).

### Task 1.4: Route it
- [ ] **Step 1:** Add route `/practice/grammar` → `<GrammarPractice />` in `App.tsx`.
- [ ] **Step 2:** Verify the page renders identically to `grammar-app.html` open-in-browser (same question, same interactions).

**Checkpoint:** Update `project_student-app-react-rebuild.md` memory — Chunk 1 done, grammar app ported.

---

## Chunk 2 — New pages (skeletons + real data where endpoints exist)

**Objective:** Add the 5-6 new pages with nav. Wire to existing endpoints first; endpoints added in Chunk 3 fill the gaps.

### Task 2.1: Dashboard page
- [ ] **Step 1:** Create `FRONTEND/src/pages/DashboardPage.tsx` — home at `/`. Show: overall accuracy (from `fetchStats`), quick-start buttons to each mode, recent activity. Use React Query.
- [ ] **Step 2:** Move `PracticePage` to `/practice` so `/` is the dashboard.

### Task 2.2: Diagnostic page
- [ ] **Step 1:** Create `FRONTEND/src/pages/DiagnosticPage.tsx` at `/diagnostic`. Runs a short adaptive assessment across domains, then surfaces weak concepts. Calls `/study/recommendations` for the result summary.
- [ ] **Step 2:** Create `FRONTEND/src/api/diagnostic.ts` (stub in Chunk 3 if endpoint missing).

### Task 2.3: Test mode page
- [ ] **Step 1:** Create `FRONTEND/src/pages/TestModePage.tsx` at `/test`. Full-length timed simulation (33q/32min — matches existing `3a5e944` test-mode backend work). Reuse `TestTimer` + `QuestionCard`.
- [ ] **Step 2:** Fetch via `/questions` with test-mode params; submit batch on complete.

### Task 2.4: Weak concepts page
- [ ] **Step 1:** Create `FRONTEND/src/pages/WeakConceptsPage.tsx` at `/weak-concepts`. Lists low-accuracy grammar keys / focus areas from `fetchStats` + `/study/recommendations`.
- [ ] **Step 2:** Each concept links to a filtered practice drill.

### Task 2.5: Missed questions page
- [ ] **Step 1:** Create `FRONTEND/src/pages/MissedQuestionsPage.tsx` at `/missed`. Lists questions the user got wrong, allows re-attempt. Needs new backend endpoint (Chunk 3, Task 3.1).
- [ ] **Step 2:** Create `FRONTEND/src/api/study.ts` with `fetchMissedQuestions`, `fetchRecommendations`, `requestGeneration`.

### Task 2.6: Nav + routes
- [ ] **Step 1:** Update `App.tsx` NavBar with links: Dashboard, Practice, Diagnostic, Test, Stats, Weak Concepts, Missed.
- [ ] **Step 2:** Add all routes to `Routes`.

**Checkpoint:** Update memory — Chunk 2 done, 5-6 pages scaffolded and wired to existing endpoints.

---

## Chunk 3 — Backend `student.py` extensions

**Objective:** Add only the endpoints the new pages need that don't already exist.

### Task 3.1: Missed-questions endpoint
- [ ] **Step 1:** Add `GET /study/missed/{user_id}` to `student.py` — returns questions where the user's latest answer was wrong, paginated, with option + annotation context.
- [ ] **Step 2:** Add response model to `backend/app/models/payload.py`.
- [ ] **Step 3:** Test in `backend/tests/test_student_router.py`.

### Task 3.2: Diagnostic summary endpoint (if needed)
- [ ] **Step 1:** Evaluate whether `/study/recommendations` already covers the diagnostic summary. If yes, skip. If no, add `POST /diagnostic/submit` that scores a diagnostic batch and returns weak-concept ranking.
- [ ] **Step 2:** Test.

### Task 3.3: Dynamic grammar-question fetch
- [ ] **Step 1:** Confirm `/questions` returns the grammar-key / trap metadata that `GrammarPractice` needs (from QuestionAnnotation). If the response shape is missing fields, extend the `/questions` response model — do NOT change the 11 frontend function signatures.
- [ ] **Step 2:** Wire `GrammarPractice` to fetch from `/questions` instead of hardcoded data (replace the Chunk-1 hardcoded block with a `useQuery`).

**Checkpoint:** Update memory — Chunk 3 done, backend extended, grammar app now API-driven.

---

## Chunk 4 — Integration, polish, verification

### Task 4.1: Auth seam
- [ ] **Step 1:** Confirm all new pages route `user_token` through `FRONTEND/src/lib/auth.ts` (the single dev/prod auth seam). No hardcoded tokens in pages.
- [ ] **Step 2:** Reference `STUDENT_AUTH_PRD.md` for the drop-in plan.

### Task 4.2: Animations + loading/error states
- [ ] **Step 1:** Add Framer Motion page transitions and React Query loading/error states across all new pages.
- [ ] **Step 2:** Responsive check at mobile/tablet/desktop breakpoints.

### Task 4.3: Verification
- [ ] **Step 1:** `npm run build` clean (Vite).
- [ ] **Step 2:** `pytest backend/tests/test_student_router.py` green.
- [ ] **Step 3:** Manual: each page loads, data lands in DB verifiable via `/api/stats/{user_id}`.
- [ ] **Step 4:** Run `openwolf designqc` to screenshot the new pages; review against modern standards.

**Checkpoint:** Update memory — Chunk 4 done, plan complete. Mark `project_student-app-react-rebuild.md` as implemented.

---

## Open questions to confirm before implementation

1. **Page list final?** Dashboard, Practice, Diagnostic, Test Mode, Stats, Weak Concepts, Missed — 7 routes (2 existing + 5 new). Add/remove?
2. **Auth:** stay on the hardcoded `VITE_TEST_USER_TOKEN` for now (per existing PRD), drop in real auth later?
3. **Diagnostic design:** adaptive short test, or fixed-length? Does `/study/recommendations` already produce the weak-concept ranking we'd show?