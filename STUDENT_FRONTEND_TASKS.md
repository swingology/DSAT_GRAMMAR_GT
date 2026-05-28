# DSAT Student Frontend — Task List

**Phase execution rule:** Complete all tasks in Phase 1 and verify the smoke test before starting Phase 2. Complete Phase 2 verification checklist before starting the auth workstream (`STUDENT_AUTH_TASKS.md`).

**Auth tasks are in a separate file:** `STUDENT_AUTH_TASKS.md`

---

## Phase 1 — Core Exam Drill

### P1-01 · Scaffold frontend project
- `cd /home/jb/DSAT_REDUX_MD && npm create vite@latest frontend -- --template react-ts`
- Add Tailwind CSS, React Router v6
- Add proxy in `vite.config.ts`: `'/api': 'http://localhost:8000'`, `'/users': 'http://localhost:8000'`, `'/auth': 'http://localhost:8000'`
- Create `.env` with:
  ```
  VITE_API_BASE_URL=http://localhost:8000
  VITE_TEST_USER_TOKEN=<uuid-from-seed>
  VITE_TEST_USER_ID=<int-id-from-seed>
  ```
- Create folder structure: `src/api/`, `src/components/`, `src/pages/`, `src/lib/`, `src/types/`

### P1-02 · Seed test user
- Hit `POST /users` with `{ "name": "Test Student", "role": "student" }` (or insert directly into DB)
- Copy the returned `user_token` UUID and integer `id` into `.env`
- Verify with `GET /users/{id}` that the row exists

### P1-03 · Create `src/lib/auth.ts` (test-user stub)
```ts
// Stub for Phases 1–2. Auth phase replaces this body — no other file changes.
export function getUserToken(): string {
  return import.meta.env.VITE_TEST_USER_TOKEN;
}
export function getUserId(): string {
  return import.meta.env.VITE_TEST_USER_ID;
}
```
**This is the only file that changes when auth is wired up.** Every other call-site imports from here.

### P1-04 · Define TypeScript types (`src/types/index.ts`)
Match these exactly to the API response shapes:
```ts
export interface QuestionOption {
  option_label: string;
  option_text: string;
}
export interface Question {
  id: string;
  current_question_text: string;
  current_passage_text: string | null;
  options: QuestionOption[];
  grammar_role_key: string | null;
  grammar_focus_key: string | null;
  reading_skill_family_key: string | null;
  reading_focus_key: string | null;
  difficulty_overall: string | null;
  content_origin: string;
}
export interface InventoryMetadata {
  matching_target_total: number;
  matching_unseen: number;
  served: number;
  includes_generated: boolean;
  below_threshold: boolean;
  threshold: number;
}
export interface QuestionsResponse {
  items: Question[];
  inventory: InventoryMetadata;
}
export interface SubmitResult {
  id: number;
  is_correct: boolean;
}
export interface UserStats {
  total_answered: number;
  total_correct: number;
  accuracy: number;
  top_missed_focus_keys: string[];
  top_missed_trap_keys: string[];
}
```

### P1-05 · Create API module (`src/api/questions.ts`)
```ts
import { QuestionsResponse, SubmitResult } from '../types';

const BASE = import.meta.env.VITE_API_BASE_URL;

export async function fetchQuestions(params: {
  domain?: 'grammar' | 'reading';
  difficulty?: string;
  limit?: number;
  userToken: string;
}): Promise<QuestionsResponse> {
  const qs = new URLSearchParams();
  if (params.domain) qs.set('domain', params.domain);
  if (params.difficulty) qs.set('difficulty', params.difficulty);
  qs.set('limit', String(params.limit ?? 20));
  qs.set('user_token', params.userToken);
  const res = await fetch(`${BASE}/api/questions?${qs}`, {
    headers: { 'X-API-Key': import.meta.env.VITE_STUDENT_API_KEY ?? 'student' },
  });
  if (!res.ok) throw new Error(`fetchQuestions ${res.status}`);
  return res.json();
}

export async function submitAnswer(body: {
  user_token: string;
  question_id: string;
  selected_option_label: string;
}): Promise<SubmitResult> {
  const res = await fetch(`${BASE}/api/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': import.meta.env.VITE_STUDENT_API_KEY ?? 'student',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`submitAnswer ${res.status}`);
  return res.json();
}
```
**Note:** Check `backend/app/auth.py` for the exact header name and key value the `student_required` dependency expects. Add `VITE_STUDENT_API_KEY` to `.env` accordingly.

### P1-06 · Build `<QuestionCard>` component
Props: `question: Question`, `onSubmit: (label: string, result: SubmitResult) => void`

Behavior:
- Renders passage (if present) in a styled blockquote
- Renders question stem
- Renders 4 radio buttons (A–D) — labels come from `options[].option_label`, text from `options[].option_text`
- "Submit Answer" button — disabled until selection made
- On click: calls `submitAnswer()`, then calls `onSubmit(selectedLabel, result)`
- Shows feedback inline: green "Correct!" or red "Wrong — the answer was [X]"
- "Next" button appears after feedback is shown

### P1-07 · Build `<SessionSetup>` component (filter screen)
- Domain radio: Grammar / Reading / Mixed (default)
- Difficulty radio: Easy / Medium / Hard / Any (default)
- "Start Drill" button → calls `fetchQuestions()` with selections → passes `items[]` to parent

### P1-08 · Build `<SessionComplete>` component
Props: `answered: number`, `correct: number`

Displays: "Session complete — X/Y correct (Z%)" + "Start New Session" button.

### P1-09 · Build `PracticePage` and wire routing
`/` renders `<SessionSetup>` → on start, switches to drill mode, renders `<QuestionCard>` → on session end renders `<SessionComplete>`.

State machine (in `PracticePage`):
```
setup → drilling → complete
```
No routing changes needed between these states — single page, local state.

### P1-10 · Phase 1 manual smoke test
- [ ] App loads with no console errors
- [ ] Filter "Grammar / Any difficulty" → questions load, passage shown where applicable
- [ ] Select option, submit → correct/wrong feedback shown
- [ ] Next question advances; last question shows SessionComplete
- [ ] Filter "Reading / Hard" → different questions load
- [ ] Network tab: `POST /api/submit` returns `{ id, is_correct }` with HTTP 200

---

## Phase 2 — Stats & Progress Tracking

### P2-01 · Create stats API module (`src/api/stats.ts`)
```ts
import { UserStats } from '../types';
const BASE = import.meta.env.VITE_API_BASE_URL;

export async function fetchStats(userId: string): Promise<UserStats> {
  const res = await fetch(`${BASE}/api/stats/${userId}`, {
    headers: { 'X-API-Key': import.meta.env.VITE_STUDENT_API_KEY ?? 'student' },
  });
  if (!res.ok) throw new Error(`fetchStats ${res.status}`);
  return res.json();
}
```

### P2-02 · Build `<StatsPanel>` component
Props: `userId: string`

- Fetches stats on mount
- Re-fetches whenever parent calls a `refresh()` callback (pass `onRefresh` prop or use a version counter pattern)
- Shows:
  - Large accuracy % circle or number
  - "X / Y answered correctly"
  - Chip list: top missed focus keys
  - Chip list: top missed trap keys
- **Dev accordion:** collapsible `<pre>{JSON.stringify(rawStats, null, 2)}</pre>` — remove in Phase 3

### P2-03 · Wire `<StatsPanel>` into `PracticePage`
- Add `/stats` route that renders `<StatsPanel userId={getUserId()} />`
- Add a minimal nav bar: "Practice" | "Stats"
- After every `submitAnswer()` in `<QuestionCard>`, call the refresh callback so `<StatsPanel>` re-fetches (if it is mounted)

### P2-04 · Phase 2 verification checklist (all must pass)
- [ ] Open Stats page — shows 0/0 initially for fresh test user
- [ ] Submit 5 answers in Practice (mix of correct/wrong), navigate to Stats → `total_answered = 5`
- [ ] `total_correct` matches the count you knew you got right
- [ ] `accuracy` equals `total_correct / total_answered` (within 0.01 floating point)
- [ ] Submit a wrong grammar answer → `top_missed_focus_keys` includes the question's `grammar_focus_key`
- [ ] Stats update without a full page reload (just navigate to /stats after submitting)
- [ ] Raw JSON accordion shows no unexpected `null` or missing fields

---

## Implementation Order (strict)

```
P1-01 → P1-02 → P1-03 → P1-04 → P1-05 → P1-06 → P1-07 → P1-08 → P1-09 → P1-10 smoke test
                    ↓ (smoke test passes)
P2-01 → P2-02 → P2-03 → P2-04 verification checklist
                    ↓ (checklist passes)
→ continue in STUDENT_AUTH_TASKS.md
```

---

## Key Integration Notes

1. **API key header:** The `student_required` dependency in `auth.py` reads `X-API-Key`. Confirm the exact expected value by reading `backend/app/config.py` — add it to `.env` as `VITE_STUDENT_API_KEY`.

2. **`practice_status` filter:** `GET /api/questions` only returns questions with `practice_status = 'active'`. If the question list comes back empty, the DB likely has no approved/active questions — check with `GET /admin/questions?status=active&limit=5`.

3. **`options[]` shape:** The `options` array in `StudentQuestionResponse` is `List[dict]` — confirm actual keys returned (`option_label`, `option_text`) by logging the first raw response before building `<QuestionCard>`.

4. **`user_token` vs `user_id`:** The submit endpoint takes a `user_token` UUID (not the integer `id`). The stats endpoint takes the integer `user_id`. Keep both in env/auth module.

5. **CORS:** If running frontend on port 5173 and backend on 8000, ensure `BACKEND_CORS_ORIGINS` in `config.py` includes `http://localhost:5173`.
