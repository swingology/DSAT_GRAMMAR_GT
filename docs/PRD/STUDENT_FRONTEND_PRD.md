# DSAT Student Practice Frontend — PRD

**Version:** 1.2  
**Date:** 2026-05-28  
**Scope:** Student-facing web app for DSAT verbal exam prep — core drill and stats only  
**Backend:** FastAPI at `http://localhost:8000` (existing, unchanged)  
**Auth:** Handled separately — see `STUDENT_AUTH_PRD.md`

---

## Overview

A lightweight React/TypeScript frontend that lets students drill DSAT verbal questions, see immediate feedback, and track their accuracy over time. Built in two strictly-ordered phases so that each phase is provably working before the next begins. Auth is a separate workstream (`STUDENT_AUTH_PRD.md`) that drops in after Phase 2 is verified.

---

## Guiding Principles

1. **Backend-first integration.** Every UI component is wired to a real API call — no local mocks, no fake data.
2. **Test user instead of auth.** Both phases use a hardcoded test user (`user_token` UUID stored in `.env`) so that auth complexity does not block core function verification.
3. **Stats must be verifiable.** After each answer submission the DB count must be inspectable (via `/api/stats/{user_id}`) to confirm data is landing correctly before moving on.
4. **Auth is a drop-in.** The auth layer replaces the hardcoded `user_token` at a single call-site (`src/lib/auth.ts`); no other component changes. See `STUDENT_AUTH_PRD.md`.
5. **No speculative features.** Build exactly what is listed. Nothing else.

---

## Phase 1 — Core Exam Drill (no auth, test user)

### Goal
A student can load questions, read them, pick an answer, and see whether they were correct.

### Screens

#### 1. Practice Session Screen
- Domain selector: **Grammar** | **Reading** | **Mixed** (maps to `?domain=grammar|reading` or omit)
- Difficulty selector: **Easy** | **Medium** | **Hard** | **Any**
- "Start Drill" button → fetches `GET /api/questions` with chosen filters
- Displays one question at a time from the returned list

#### 2. Question Card
- Passage text (if present) rendered above question text; preserve line breaks
- Question stem
- Four radio-button options (A–D) from `options[]` array
- "Submit" button — disabled until an option is selected
- On submit → calls `POST /api/submit`
- Reveals: ✓ correct / ✗ wrong + which answer was correct
- "Next Question" button advances to the next item in the fetched list
- When list is exhausted → "Session Complete" state with a summary (questions answered, correct count, accuracy %)

### API Calls (Phase 1)
| Action | Endpoint | Key params |
|--------|----------|------------|
| Fetch questions | `GET /api/questions` | `domain`, `difficulty`, `limit=20`, `user_token` (test token for exclude_seen) |
| Submit answer | `POST /api/submit` | `user_token`, `question_id`, `selected_option_label` |

### Test User Setup
- Create one `User` row via `POST /users` (or direct DB seed) with a known `user_token` UUID
- Store as `VITE_TEST_USER_TOKEN=<uuid>` in `.env`
- All `user_token` fields in API calls read from this env var
- **No login UI in this phase**

---

## Phase 2 — Stats & Progress Tracking

### Goal
Verify that submitted answers are accumulating correctly in the DB, and surface that data to the student.

### Screens

#### 3. Stats Panel (sidebar or dedicated route `/stats`)
- Calls `GET /api/stats/{user_id}` on mount and after every submission
- Displays:
  - Total answered
  - Total correct
  - Accuracy % (large, prominent)
  - Top missed grammar focus keys (chip list)
  - Top missed trap keys (chip list)
- **Dev verification mode:** a collapsible raw JSON accordion showing the full API response — confirms data is landing before styling hides it

#### 4. Study Recommendations (optional, Phase 2 stretch)
- Button: "What should I study?" → `POST /api/study/recommendations`
- Body: `{ user_token, limit: 5 }`
- Renders returned weak-area list as a "Focus On:" card

### API Calls (Phase 2)
| Action | Endpoint |
|--------|----------|
| Fetch stats | `GET /api/stats/{user_id}` |
| Get recommendations | `POST /api/study/recommendations` |

### Verification Checklist (must pass before Phase 3)
- [ ] Submit 5 answers (mix of correct/wrong), confirm `total_answered` increments correctly
- [ ] Submit a wrong answer on a grammar question, confirm `top_missed_focus_keys` reflects it
- [ ] Accuracy % matches manual calculation
- [ ] Stats panel updates immediately after each submission (TanStack Query `invalidateQueries` on submit mutation — not stale)

---

## Technical Stack

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Framework | React 18 + TypeScript | — |
| Build tool | Vite | — |
| Styling | Tailwind CSS + **shadcn/ui** | Accessible radio buttons, buttons, and form controls out of the box (Radix UI primitives); avoids hand-rolling keyboard/focus handling on the question card |
| Routing | React Router v6 | 3 routes — TanStack Router type-safety not worth the overhead |
| Data fetching | **TanStack Query (React Query v5)** | Handles the stats re-fetch-after-submit pattern, loading/error states, and caching without manual `useEffect` boilerplate |
| HTTP client | native `fetch` inside query/mutation fns | No Axios needed |
| State | React `useState` / `useReducer` | Session drill state is local to `PracticePage` — no Redux/Zustand |
| Auth | Supabase JS client — separate phase, see `STUDENT_AUTH_PRD.md` | — |

### Key dependency list
```
react, react-dom, typescript
vite, @vitejs/plugin-react
tailwindcss, tailwindcss-animate
@radix-ui/react-* (via shadcn/ui)
@tanstack/react-query
react-router-dom
@supabase/supabase-js   # Phase 3 only
```

### Project structure
```
frontend/
  src/
    api/           # typed fetch fns (used as queryFn / mutationFn)
    components/    # QuestionCard, OptionButton, StatsPanel, SessionSummary (shadcn primitives inside)
    pages/         # PracticePage, StatsPage, LoginPage (Phase 3)
    lib/
      auth.ts      # getUserToken() stub — returns VITE_TEST_USER_TOKEN (replaced in auth phase)
      query.ts     # QueryClient singleton
    types/         # TypeScript interfaces matching API response shapes
  .env             # VITE_API_BASE_URL, VITE_TEST_USER_TOKEN, VITE_TEST_USER_ID, VITE_STUDENT_API_KEY
```

---

## Out of Scope

- Admin UI (separate project)
- Timed exam simulation (future feature)
- AI study set generation UI (future feature — endpoint exists, UI deferred)
- Native mobile app
- Any backend changes

---

## Success Criteria

| Phase | Done when |
|-------|-----------|
| 1 | Can drill 20 questions end-to-end; correct/wrong feedback shown; no console errors |
| 2 | Stats panel shows accurate counts after each submission; passes full verification checklist |
| Auth | See `STUDENT_AUTH_PRD.md` — begins only after Phase 2 is verified |
