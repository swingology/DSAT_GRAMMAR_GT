# DSAT Student Frontend — Task List

**Phase execution rule:** Complete all tasks in Phase 1 and verify the smoke test before starting Phase 2. Complete Phase 2 verification checklist before starting the auth workstream (`STUDENT_AUTH_TASKS.md`).

**Auth tasks are in a separate file:** `STUDENT_AUTH_TASKS.md`

---

## Phase 1 — Core Exam Drill

### P1-01 · Scaffold frontend project
- `cd /home/jb/DSAT_REDUX_MD && npm create vite@latest frontend -- --template react-ts`
- Install dependencies:
  ```bash
  cd frontend
  npm install react-router-dom @tanstack/react-query
  npm install -D tailwindcss @tailwindcss/vite tailwindcss-animate
  npx shadcn@latest init   # choose "Default" style, Tailwind CSS, src/lib/utils.ts path
  npx shadcn@latest add button radio-group accordion
  ```
- `vite.config.ts` — **no proxy needed**; fetch calls use `VITE_API_BASE_URL` directly and backend CORS allows `*`
- Create `.env` with:
  ```
  VITE_API_BASE_URL=http://localhost:8000
  VITE_STUDENT_API_KEY=<one key from backend STUDENT_API_KEYS>
  VITE_TEST_USER_TOKEN=<uuid-from-seed>
  VITE_TEST_USER_ID=<int-id-from-seed>
  ```
- Create folder structure: `src/api/`, `src/components/`, `src/pages/`, `src/lib/`, `src/types/`
- Create `src/lib/query.ts`:
  ```ts
  import { QueryClient } from '@tanstack/react-query';
  export const queryClient = new QueryClient();
  ```
- Wrap `<App>` in `main.tsx`:
  ```tsx
  import { QueryClientProvider } from '@tanstack/react-query';
  import { queryClient } from './lib/query';
  // ...
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
  ```

### P1-02 · Seed test user
- Hit `POST /users` with the **admin API key** (not the student key):
  ```bash
  curl -X POST http://localhost:8000/users \
    -H "X-API-Key: <one key from backend ADMIN_API_KEYS>" \
    -H "Content-Type: application/json" \
    -d '{ "username": "test-student" }'
  ```
  The admin key value is in `backend/.env` as `ADMIN_API_KEYS` (or check `backend/app/config.py`).
- Copy the returned `user_token` UUID and integer `id` into `frontend/.env`
- Verify with `GET /users/{id}` (admin key required) that the row exists

### P1-03 · Create `src/lib/auth.ts` (test-user stub)
```ts
// Stub for Phases 1–2. Auth phase replaces this body and awaits the two API call sites.
export function getUserToken(): string {
  return import.meta.env.VITE_TEST_USER_TOKEN;
}
export function getUserId(): string {
  return import.meta.env.VITE_TEST_USER_ID;
}
```
**`lib/auth.ts` is the primary seam.** In Phase 3 (A-06), both getters become `async` and return `Promise<string>`. You will also need to add `await` at the two call sites in `api/questions.ts` and `api/stats.ts` — no other files change.

### P1-04 · Define TypeScript types (`src/types/index.ts`)
Match these exactly to the API response shapes:
```ts
export interface QuestionOption {
  label: string;   // matches GET /api/questions response (backend serializes as label/text)
  text: string;
}
export interface Question {
  id: string;
  content_origin: string;
  current_question_text: string;
  current_passage_text: string | null;
  passage_tokens: Record<string, unknown>[] | null;
  practice_status: string;
  options: QuestionOption[];
  grammar_role_key: string | null;
  grammar_focus_key: string | null;
  reading_skill_family_key: string | null;
  reading_focus_key: string | null;
  difficulty_overall: string | null;
  stimulus_mode_key: string | null;
  source_exam_code: string | null;
  source_subject_code: string | null;
  source_section_code: string | null;
  source_module_code: string | null;
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
export interface WeaknessTarget {
  domain: string;
  focus_key: string;
  skill_family_key: string | null;
  grammar_role_key: string | null;
  difficulty: string;
  weakness_score: number;
  miss_count: number;
  attempt_count: number;
  miss_rate: number;
  days_since_last_attempt: number;
  inventory_unseen: number;
  inventory_below_threshold: boolean;
}
export interface StudyRecommendationsResponse {
  user_id: number;
  top_targets: WeaknessTarget[];
  threshold: number;
}
```

### P1-05 · Create API module (`src/api/questions.ts`)
```ts
import { QuestionsResponse, SubmitResult } from '../types';

const BASE = import.meta.env.VITE_API_BASE_URL;
const STUDENT_API_KEY = import.meta.env.VITE_STUDENT_API_KEY;

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
    headers: { 'X-API-Key': STUDENT_API_KEY },
  });
  if (!res.ok) {
    if (res.status === 403) throw new Error('INVALID_API_KEY');
    throw new Error(`fetchQuestions ${res.status}`);
  }
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
      'X-API-Key': STUDENT_API_KEY,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`submitAnswer ${res.status}`);
  return res.json();
}
```

**Usage with TanStack Query** — in `PracticePage` use `useMutation`:
```ts
const submitMutation = useMutation({
  mutationFn: submitAnswer,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['stats'] }),
  onError: () => { /* re-enable submit button */ },
});
```

**Error states to handle in consuming components:**
- `INVALID_API_KEY` error → display "Invalid API key — check VITE_STUDENT_API_KEY in .env"
- `items[]` empty after fetch → display "No active questions for these filters"
- `items[]` exhausted (index >= length) → trigger SessionComplete state
- Fetch network failure → display retry button, do not crash
- Submit 4xx/5xx → re-enable submit button, display inline error message

**Note:** `VITE_STUDENT_API_KEY` should already be in `.env` from P1-01. Confirm the value by reading `backend/app/config.py` → `student_api_keys` / `student_api_key_list`.

### P1-06 · Build `<QuestionCard>` component
Props:
```ts
{
  question: Question;
  onSubmitAnswer: (label: string) => Promise<SubmitResult>;
  onAnswered: (label: string, result: SubmitResult) => void;
  onNext: () => void;
}
```

Use shadcn `RadioGroup` + `RadioGroupItem` for options and shadcn `Button` for submit/next.

Behavior:
- Renders passage (if present) in a styled blockquote
- Renders question stem
- Renders 4 radio buttons (A–D) — labels come from `options[].label`, text from `options[].text`
- "Submit Answer" button — disabled until selection made
- On click: calls `onSubmitAnswer(selectedLabel)`, then calls `onAnswered(selectedLabel, result)`
- Shows feedback inline: green "Correct! ✓" or red "Incorrect ✗"
  - **Note:** The student API intentionally omits the correct answer label (`POST /api/submit` returns `{id, is_correct}` only). Do not attempt to reveal the correct option.
- "Next Question" button appears after feedback; parent (`PracticePage`) advances the index via `onNext`
- While submit is in-flight: disable button, show loading state
- On submit error: re-enable button, show "Submission failed — try again"

### P1-07 · Build `<SessionSetup>` component (filter screen)
- Domain radio: Grammar / Reading / Mixed (default)
- Difficulty radio: Easy / Medium / Hard / Any (default)
- "Start Drill" button → calls `fetchQuestions()` with selections → passes `items[]` to parent

### P1-11 · Dynamic filter options — only show domains and difficulties with active questions

**Why:** Domain filter on the backend uses `grammar_role_key` (grammar) and `reading_skill_family_key` (reading) — both null in current data, so selecting either returns 0 results. Hardcoded options mislead the user. Probe the API at mount time and render only options that have inventory.

**Approach:** 3 parallel probes on `SessionSetup` mount, all with `limit=1` (or `limit=50` for difficulties):

```ts
// src/api/inventory.ts
export interface FilterInventory {
  hasGrammar: boolean;
  hasReading: boolean;
  hasMixed: boolean;  // always true if any active questions exist
  difficulties: string[];  // distinct non-null values from sample
}

export async function fetchFilterInventory(userToken: string): Promise<FilterInventory> {
  const [mixed, grammar, reading] = await Promise.all([
    fetch(`${BASE}/api/questions?limit=50&user_token=${userToken}`, { headers }),
    fetch(`${BASE}/api/questions?domain=grammar&limit=1&user_token=${userToken}`, { headers }),
    fetch(`${BASE}/api/questions?domain=reading&limit=1&user_token=${userToken}`, { headers }),
  ]);
  const [mixedData, grammarData, readingData] = await Promise.all([
    mixed.json(), grammar.json(), reading.json(),
  ]);
  const difficulties = [...new Set(
    mixedData.items
      .map((q: Question) => q.difficulty_overall)
      .filter(Boolean)
  )] as string[];
  return {
    hasMixed: mixedData.inventory.matching_target_total > 0,
    hasGrammar: grammarData.inventory.matching_target_total > 0,
    hasReading: readingData.inventory.matching_target_total > 0,
    difficulties,
  };
}
```

**`SessionSetup` changes:**
- Add `useQuery({ queryKey: ['filter-inventory'], queryFn: () => fetchFilterInventory(getUserToken()) })`
- While loading: show skeleton / disabled "Start Drill" button
- Domain options: render each only if its flag is true; always render Mixed if `hasMixed`
- Difficulty options: render "Any" always + one chip per value in `difficulties`; if `difficulties` is empty, show "Any" only
- If selected domain/difficulty becomes unavailable (e.g. user navigated away and inventory changed), reset to default
- Error: if inventory probe fails, fall back to showing all options (fail open)

**Files touched:** `src/api/inventory.ts` (new), `src/components/SessionSetup.tsx` (update)

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
- [ ] Filter "Reading / Any difficulty" → questions load (10 active reading questions in DB)
- [ ] Select option, submit → correct ✓ or incorrect ✗ feedback shown inline
- [ ] Next question advances; last question (10/10) shows SessionComplete
- [ ] Filter "Reading / Medium" → subset of questions loads (6 medium-difficulty questions)
- [ ] Filter "Grammar / Any" → shows "No active questions" error message (expected — no grammar questions active yet)
- [ ] Network tab: `POST /api/submit` returns `{ id, is_correct }` with HTTP 200
- [ ] Note: passages will not render even on `passage_excerpt` questions — `current_passage_text` is null in current data (ingestion gap, not a frontend bug)

---

## Phase 2 — Stats & Progress Tracking

### P2-01 · Create stats API module (`src/api/stats.ts`)
```ts
import { UserStats } from '../types';
const BASE = import.meta.env.VITE_API_BASE_URL;
const STUDENT_API_KEY = import.meta.env.VITE_STUDENT_API_KEY;

export async function fetchStats(userId: string): Promise<UserStats> {
  const res = await fetch(`${BASE}/api/stats/${userId}`, {
    headers: { 'X-API-Key': STUDENT_API_KEY },
  });
  if (!res.ok) throw new Error(`fetchStats ${res.status}`);
  return res.json();
}
```

### P2-02 · Build `<StatsPanel>` component
Props: `userId: string`

- Fetches stats using `useQuery({ queryKey: ['stats', userId], queryFn: () => fetchStats(userId) })`
- Auto-refetches when `submitMutation` in `PracticePage` calls `queryClient.invalidateQueries({ queryKey: ['stats'] })` on success — no manual refresh callback needed
- Shows:
  - Large accuracy % circle or number
  - "X / Y answered correctly"
  - Chip list: top missed focus keys
  - Chip list: top missed trap keys
- **Dev accordion:** collapsible `<pre>{JSON.stringify(rawStats, null, 2)}</pre>` — remove in Phase 3

### P2-03 · Wire stats route and query invalidation
- Create `StatsPage` that renders `<StatsPanel userId={getUserId()} />`
- Add `/stats` route for `StatsPage`
- Add a minimal nav bar: "Practice" | "Stats"
- In `PracticePage`, own the submit mutation and pass `onSubmitAnswer` into `<QuestionCard>`
- On every successful `submitAnswer()`, call `queryClient.invalidateQueries({ queryKey: ['stats'] })` so `/stats` is fresh after navigation and any mounted stats panel re-fetches

### P2-04 · Phase 2 verification checklist (all must pass)
- [ ] Open Stats page — shows 0/0 initially for fresh test user
- [ ] Submit 5 answers in Practice (mix of correct/wrong), navigate to Stats → `total_answered = 5`
- [ ] `total_correct` matches the count you knew you got right
- [ ] `accuracy` equals `total_correct / total_answered` (within 0.01 floating point)
- [ ] Submit a wrong **reading** answer → `top_missed_focus_keys` includes the question's `reading_focus_key` (e.g. `underlined_word_meaning`, `main_purpose`)
  - Note: no active grammar questions exist yet — `grammar_focus_key` is null on all current questions; test reading keys instead
- [ ] Stats update without a full page reload (just navigate to /stats after submitting)
- [ ] Raw JSON accordion shows no unexpected `null` or missing fields

### P2-05 · Optional Phase 2 stretch: study recommendations
This is explicitly optional in the PRD and is **not** a gate for moving to `STUDENT_AUTH_TASKS.md`.

- Create `src/api/recommendations.ts`
  ```ts
  import { StudyRecommendationsResponse } from '../types';

  const BASE = import.meta.env.VITE_API_BASE_URL;
  const STUDENT_API_KEY = import.meta.env.VITE_STUDENT_API_KEY;

  export async function fetchStudyRecommendations(body: {
    user_token: string;
    limit?: number;
  }): Promise<StudyRecommendationsResponse> {
    const res = await fetch(`${BASE}/api/study/recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': STUDENT_API_KEY,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`fetchStudyRecommendations ${res.status}`);
    return res.json();
  }
  ```
- Add a "What should I study?" button to `StatsPage` or `StatsPanel`
- On click, call `fetchStudyRecommendations({ user_token: getUserToken(), limit: 5 })`
- Render returned `top_targets[]` as a compact "Focus On" list
- Backend note: current `StudyRecommendationsRequest` only requires `user_token`; `limit` is PRD-level UI intent and is safe to omit if the backend rejects extra fields

---

## Implementation Order (strict)

```
P1-01 → P1-02 → P1-03 → P1-04 → P1-05 → P1-06 → P1-07 → P1-08 → P1-09 → P1-10 smoke test
                    ↓ (smoke test passes)
P2-01 → P2-02 → P2-03 → P2-04 verification checklist
                    ↓ (checklist passes)
→ continue in STUDENT_AUTH_TASKS.md

Optional: P2-05 can be done before auth if desired, but it is not part of the strict gate.
```

---

## Key Integration Notes

1. **API key header:** The `student_required` dependency in `auth.py` reads `X-API-Key`. Confirm the exact expected value by reading `backend/app/config.py` — add it to `.env` as `VITE_STUDENT_API_KEY`.

2. **`practice_status` filter:** `GET /api/questions` only returns questions with `practice_status = 'active'`. If the question list comes back empty, the DB likely has no approved/active questions — check with `GET /admin/questions?status=active&limit=5`.

3. **`options[]` shape:** The backend serializes options as `{"label": ..., "text": ...}` (see `student.py` line ~297). The `QuestionOption` TypeScript type uses `label` / `text` to match this. Do not use `option_label` / `option_text`.

4. **`user_token` vs `user_id`:** The submit endpoint takes a `user_token` UUID (not the integer `id`). The stats endpoint takes the integer `user_id`. Keep both in env/auth module.

5. **CORS:** If running frontend on port 5173 and backend on 8000 with direct `VITE_API_BASE_URL` calls, ensure `CORS_ALLOWED_ORIGINS` in backend config includes `http://localhost:5173` or is `*`.

6. **Active question inventory (as of first test run):** 10 questions active, all reading, all official.
   Verified filter values from `/api/questions`:
   ```
   domain            reading (all) — grammar returns empty
   difficulty        medium (6), null (4) — easy/hard return empty
   reading_focus_key underlined_word_meaning, main_purpose, central_idea,
                     sentence_function, structural_pattern, null
   grammar_focus_key null (all) — no active grammar questions
   stimulus_mode_key passage_excerpt (9), sentence_only (1)
   ```
   SessionSetup filter options are **hardcoded** — selecting `grammar`, `easy`, or `hard` will hit the
   empty-results error state (handled gracefully). To show only valid options, a `/api/inventory`
   endpoint returning distinct active values would be needed.

7. **Passage text gap:** All 10 active questions have `stimulus_mode_key = passage_excerpt` but
   `current_passage_text = null`. Passages were not ingested into these records (data pipeline gap,
   not a frontend bug). The `<QuestionCard>` passage blockquote will not render for any current
   questions. This will resolve once the full ingestion pipeline runs on the official PDFs.
