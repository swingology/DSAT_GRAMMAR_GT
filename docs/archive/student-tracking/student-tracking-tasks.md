# Student Tracking Backend — Detailed Task List

## Phase 2.5: Question Type & Distractor Trap Analysis

**Total Estimated Effort:** ~2 weeks (10 days)  
**Timeline:** Jul 27 – Aug 10, 2024  
**Status:** Not Started

---

## TIER 1: Foundation (Days 1-4)

### 🔴 Critical Path: Frontend Data Flow

#### TASK-001: Extract Trap Type in useGrammarSession Hook
- **File:** `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`
- **Effort:** 1 day
- **Dependency:** None
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Read useGrammarSession.ts to understand current submitAnswer flow
  - **Context:** Lines ~200-230, submitAnswer uses api.submitAnswer()
  - **Criteria:** Understand current parameters passed to backend

- [ ] Locate where selected option is identified (selectAnswer function)
  - **Context:** Lines ~130-140, state.question.options.find()
  - **Criteria:** Identify how to access selected option object

- [ ] Extract distractor_type_key from selected QuestionOption
  - **Code Change:**
    ```typescript
    // In selectAnswer() before calling api.submitAnswer():
    const selectedOption = (state.question as any).options.find(
      (o: any) => o.label === optionId
    )
    const trapType = selectedOption?.distractor_type_key || null
    ```
  - **Criteria:** trapType is String or null

- [ ] Update api.submitAnswer() call to include missed_syntactic_trap_key
  - **Code Change:**
    ```typescript
    const result = await api.submitAnswer({
      question_id: (state.question as any).id,
      selected_option_label: optionId,
      user_token: USER_TOKEN,
      missed_grammar_focus_key: (state.question as any).grammar_focus_key,
      missed_syntactic_trap_key: trapType,  // ✅ ADD THIS
    })
    ```
  - **Criteria:** API receives trap_type parameter

- [ ] Test with grammar practice questions
  - **Manual Test:** Answer wrong answer, verify network tab shows missed_syntactic_trap_key
  - **Success:** Network request includes trap field

- [ ] Update TypeScript types in useGrammarSession if needed
  - **File:** `src/types/grammar.ts` or similar
  - **Criteria:** No TypeScript errors

**Acceptance Criteria:**
- ✅ TypeScript compiles without errors
- ✅ Network request to /api/submit includes `missed_syntactic_trap_key`
- ✅ Value is either trap type string or null (not undefined)
- ✅ Existing functionality (answer submission) still works
- ✅ Grammar practice questions can be answered

---

#### TASK-002: Extract Trap Type in DiagnosticTab
- **File:** `APP/STUDENT_APP_REDUX/src/components/dashboard/DiagnosticTab.tsx`
- **Effort:** 0.5 days
- **Dependency:** TASK-001 knowledge
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Locate DiagnosticQuestionCard's choose() function
  - **Context:** Lines ~35-56, submitAnswer.mutate()
  - **Criteria:** Understand current trap submission

- [ ] Extract distractor_type_key from question.options
  - **Code Change:**
    ```typescript
    function choose(label: string) {
      if (selected) return
      setSelected(label)
      
      const selectedOpt = question.options.find(o => o.label === label)
      const trapType = selectedOpt?.distractor_type_key || null
      
      submitAnswer.mutate(
        {
          question_id: question.id,
          selected_option_label: label,
          missed_grammar_focus_key: question.grammar_focus_key,
          missed_reading_focus_key: question.reading_focus_key,
          missed_syntactic_trap_key: trapType,  // ✅ ADD THIS
        },
        ...
      )
    }
    ```
  - **Criteria:** trapType extracted and passed

- [ ] Test with diagnostic session
  - **Manual Test:** Run diagnostic, answer questions, check network
  - **Success:** Diagnostic answers include trap data

**Acceptance Criteria:**
- ✅ TypeScript compiles
- ✅ Network requests include `missed_syntactic_trap_key`
- ✅ Diagnostic session still works
- ✅ Results still display correctly

---

#### TASK-003: Update API Client Types
- **File:** `APP/STUDENT_APP_REDUX/src/api/client.ts`
- **Effort:** 0.5 days
- **Dependency:** TASK-001, TASK-002
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Find submitAnswer API type definition
  - **Context:** Search for `submitAnswer` function signature
  - **Criteria:** Located in client.ts

- [ ] Add `missed_syntactic_trap_key?: string` to params
  - **Code Change:**
    ```typescript
    export async function submitAnswer(params: {
      question_id: string
      selected_option_label: string
      missed_grammar_focus_key?: string
      missed_reading_focus_key?: string
      missed_syntactic_trap_key?: string  // ✅ ADD THIS
    }) {
      return post('/api/submit', params)
    }
    ```
  - **Criteria:** TypeScript type updated

- [ ] Verify no TypeScript errors in app
  - **Command:** `npm run lint` or `tsc --noEmit` in STUDENT_APP_REDUX dir
  - **Success:** No errors

**Acceptance Criteria:**
- ✅ TypeScript compiles across entire app
- ✅ API client has correct type signature
- ✅ No unused param warnings

---

#### TASK-004: Backend Type Updates
- **File:** `backend/app/models/payload.py`
- **Effort:** 0.5 days
- **Dependency:** None (frontend can wait)
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Find UserProgressCreate type definition
  - **Context:** Search for class/type that receives POST /api/submit
  - **Criteria:** Located in payload.py

- [ ] Verify `missed_syntactic_trap_key` already exists in UserProgressCreate
  - **Expected:** Already defined as `missed_syntactic_trap_key: Optional[str] = None`
  - **Criteria:** Field exists in schema

- [ ] If not present, add field
  - **Code:** Add `missed_syntactic_trap_key: Optional[str] = None` to class
  - **Criteria:** Field in schema

- [ ] Verify submit_answer() endpoint accepts the field
  - **File:** `backend/app/routers/student.py:474`
  - **Expected:** Line ~547 already has: `missed_syntactic_trap_key=body.missed_syntactic_trap_key`
  - **Criteria:** Endpoint stores it in UserProgress

**Acceptance Criteria:**
- ✅ Backend accepts `missed_syntactic_trap_key` parameter
- ✅ UserProgress.missed_syntactic_trap_key gets populated
- ✅ No validation errors

---

### 🔵 Verification: End-to-End Data Flow

#### TASK-005: Manual Integration Test
- **Effort:** 1 day
- **Dependency:** TASK-001, TASK-002, TASK-003, TASK-004
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Start dev stack
  - **Command:** `/dev-stack` or equivalent
  - **Success:** Frontend at 5173, backend at 8000, db at 5434

- [ ] Create test user account
  - **Manual:** Register or use existing test token
  - **Criteria:** Have user_token for API calls

- [ ] Load grammar practice question
  - **Step:** Navigate to `/practice/grammar`
  - **Criteria:** Question loads

- [ ] Answer a grammar question incorrectly
  - **Step:** Click wrong answer option
  - **Criteria:** Question submits

- [ ] Check network request includes trap data
  - **Tool:** Browser DevTools Network tab
  - **Search:** Find POST /api/submit request
  - **Verify:** `missed_syntactic_trap_key` field present and has value
  - **Criteria:** Trap type is not null

- [ ] Check database for stored trap
  - **Command:** 
    ```sql
    SELECT question_id, selected_option_label, missed_syntactic_trap_key, is_correct 
    FROM user_progress 
    WHERE user_id = <test_user_id> 
    ORDER BY timestamp DESC LIMIT 1;
    ```
  - **Criteria:** missed_syntactic_trap_key is populated

- [ ] Run diagnostic session
  - **Step:** Navigate to `/` → click "Start Diagnostic"
  - **Step:** Answer 8 questions
  - **Verify:** All answers in DB have trap data
  - **Command:**
    ```sql
    SELECT COUNT(*) as total, 
           COUNT(missed_syntactic_trap_key) as with_trap 
    FROM user_progress 
    WHERE user_id = <test_user_id> 
    AND timestamp > NOW() - INTERVAL 10 MINUTES;
    ```
  - **Criteria:** with_trap = total (100% have trap data)

- [ ] Test grammar focus key + trap key are both present
  - **Command:**
    ```sql
    SELECT missed_grammar_focus_key, missed_syntactic_trap_key 
    FROM user_progress 
    WHERE user_id = <test_user_id> 
    ORDER BY timestamp DESC LIMIT 5;
    ```
  - **Criteria:** Both columns populated for each row

**Acceptance Criteria:**
- ✅ Frontend sends trap data in network request
- ✅ Backend receives and stores trap data
- ✅ Database has trap type for all test answers
- ✅ Both focus_key and trap_key are populated
- ✅ No errors in browser console or server logs (only a benign extension-noise line, see below)

**Verified 2026-07-05 (API + code level, then live browser click-through):**
- Dev stack confirmed running on non-default ports: backend `:8002`, frontend `:5174`, db `:5437` (see `.wolf/cerebrum.md`).
- `POST /api/submit` with a wrong answer stored `missed_syntactic_trap_key` + `missed_grammar_focus_key` together in `user_progress` (row id 14).
- Code-read confirmed `useGrammarSession.ts:275` and `DiagnosticTab.tsx:43-63` extract `distractor_type_key` from the selected option into the exact same payload shape used in the manual test — the frontend wiring from TASK-001/002/003 is real, not just documented.
- Ran a full diagnostic session via `/api/diagnostic/start` → `submit` ×3 → `complete`: 2 wrong answers both got `missed_syntactic_trap_key` populated (100% coverage), 1 correct answer correctly got `NULL` trap (defense-in-depth logic at `student.py:1815` confirmed). `complete` response's `breakdown.by_trap` correctly aggregated both traps.
- **Live browser click-through completed manually** (claude-in-chrome extension automation was unreliable — tab-group state kept dropping after every navigate call, ~5 failed attempts — so the user drove it directly in their own browser via Tailscale at `https://jb-2410:8443/practice/grammar`): clicked a real wrong answer on question `40e4e597-b90a-5ca1-9ee1-4e0557fb759d`, DevTools Network tab showed the `/api/submit` payload with `missed_syntactic_trap_key: "semantic_imprecision"` and `missed_grammar_focus_key: "precision_word_choice"` both populated; confirmed stored in `user_progress` (row id 20). Only console output was a benign `Unchecked runtime.lastError: The message port closed before a response was received` — standard Chrome extension messaging noise, unrelated to the app.

---

## TIER 2: Backend Analytics (Days 5-7)

### 🟢 Query Endpoint: Trap Susceptibility

#### TASK-006: Implement GET /api/student/trap-susceptibility
- **File:** `backend/app/routers/student.py` (new endpoint after line 1418)
- **Effort:** 1.5 days
- **Dependency:** TASK-005 (data flowing)
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Create response model class
  - **File:** `backend/app/models/payload.py`
  - **Class Name:** `StudentTrapSusceptibilityResponse`
  - **Fields:**
    ```python
    class StudentTrapSusceptibilityResponse(BaseModel):
        user_id: int
        total_questions_attempted: int
        
        # Per-trap metrics
        trap_encounters: Dict[str, int]  # {trap_type: count}
        trap_fall_rates: Dict[str, float]  # {trap_type: 0.0-1.0}
        trap_correct_counts: Dict[str, int]  # {trap_type: correct_count}
        
        # Rankings
        most_susceptible_traps: List[TrapMetric]
        overcoming_traps: List[TrapMetric]
        persistent_traps: List[TrapMetric]
        
        # Time-based
        trap_improvement: Dict[str, TrapImprovement]  # {trap_type: {first_5: acc, recent_5: acc, trend: float}}
    ```
  - **Criteria:** Type-safe response

- [ ] Create TrapMetric helper class
  - **Fields:** trap_type, fall_rate, occurrences, severity
  - **Criteria:** Computes severity from fall_rate

- [ ] Write SQL query to aggregate UserProgress by trap
  - **Query Logic:**
    ```python
    # SELECT missed_syntactic_trap_key, COUNT(*), SUM(is_correct)
    # FROM user_progress
    # WHERE user_id = ? AND missed_syntactic_trap_key IS NOT NULL
    # GROUP BY missed_syntactic_trap_key
    ```
  - **Criteria:** Executes without error

- [ ] Implement fall_rate calculation
  - **Formula:** fall_rate = 1 - (correct_count / total_count)
  - **Edge Cases:** Handle division by zero
  - **Criteria:** Returns 0.0-1.0 value

- [ ] Identify top 5 most susceptible traps
  - **Sort:** By fall_rate DESC
  - **Limit:** 5
  - **Criteria:** Correct ranking

- [ ] Calculate improvement trends (first 5 vs. last 5 attempts per trap)
  - **Query:** First 5 answers for each trap (ORDER BY timestamp ASC LIMIT 5)
  - **Query:** Last 5 answers for each trap (ORDER BY timestamp DESC LIMIT 5)
  - **Compute:** Accuracy change from first to last
  - **Criteria:** Shows improvement or decline

- [ ] Identify traps they're "overcoming" (improving on)
  - **Logic:** recent_accuracy > first_accuracy AND recent_accuracy >= 0.60
  - **Criteria:** Correct classification

- [ ] Identify "persistent traps" (still struggling)
  - **Logic:** recent_accuracy < 0.40 AND fall_rate > 0.60
  - **Criteria:** Correct classification

- [ ] Write endpoint function
  - **Signature:**
    ```python
    @router.get("/student/trap-susceptibility", response_model=StudentTrapSusceptibilityResponse)
    async def get_trap_susceptibility(
        db: AsyncSession = Depends(get_db),
        _auth: str = Depends(student_required),
    ):
    ```
  - **Criteria:** Endpoint accessible

- [ ] Add error handling
  - **Cases:** User not found, no attempt history, no trap data
  - **Return:** 404 for user, 200 with empty lists for no data
  - **Criteria:** Handles all error cases gracefully

- [ ] Add caching decorator (optional for Tier 2)
  - **Cache Key:** f"trap-susceptibility:{user_id}"
  - **TTL:** 1 hour
  - **Criteria:** Reduces query latency

**Acceptance Criteria:**
- ✅ Endpoint accessible at GET /api/student/trap-susceptibility
- ✅ Returns all required fields in response model
- ✅ Fall rates are accurate (verified against manual SQL)
- ✅ Top 5 traps correctly ranked
- ✅ Improvement trends correctly calculated
- ✅ Handles edge cases (no data, user not found)
- ✅ Response time < 200ms for user with 100+ attempts

---

#### TASK-007: Test GET /api/student/trap-susceptibility Endpoint
- **Effort:** 1 day
- **Dependency:** TASK-006
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Create pytest test file
  - **File:** `backend/tests/test_trap_susceptibility.py`
  - **Criteria:** File created

- [ ] Test: User with no attempts returns empty result
  - **Setup:** New user, 0 attempts
  - **Expected:** total_questions_attempted=0, empty lists
  - **Criteria:** Test passes

- [ ] Test: User with varied trap data
  - **Setup:** Create 20 test answers with different trap types
  - **Expected:** Correct grouping, accurate fall rates
  - **Criteria:** Test passes

- [ ] Test: Fall rate calculation accuracy
  - **Setup:** 10 answers, 7 correct, trap="subject_number_mismatch"
  - **Expected:** fall_rate=0.3 (1 - 7/10)
  - **Criteria:** Math correct

- [ ] Test: Top 5 ranking
  - **Setup:** Create 10 different trap types with varying fall rates
  - **Expected:** Return exactly 5, sorted by fall_rate DESC
  - **Criteria:** Test passes

- [ ] Test: Improvement detection
  - **Setup:** Trap with first 5 accuracy=0.2, last 5 accuracy=0.8
  - **Expected:** In overcoming_traps list
  - **Criteria:** Test passes

- [ ] Test: Persistent trap detection
  - **Setup:** Trap with fall_rate=0.8, recent_accuracy=0.2
  - **Expected:** In persistent_traps list
  - **Criteria:** Test passes

- [ ] Test: Authenticate with user_token
  - **Verify:** Endpoint rejects unauthenticated requests
  - **Criteria:** Returns 401/403

- [ ] Test: Response schema validation
  - **Tool:** Pydantic auto-validation
  - **Verify:** Actual response matches StudentTrapSusceptibilityResponse
  - **Criteria:** No validation errors

- [ ] Run all tests locally
  - **Command:** `pytest backend/tests/test_trap_susceptibility.py -v`
  - **Criteria:** All pass

**Acceptance Criteria:**
- ✅ Test coverage >= 90% for endpoint
- ✅ All edge cases tested
- ✅ All tests pass locally
- ✅ Response schema is correct

---

### 🟡 Additional Endpoints (Optional for Tier 2)

#### TASK-008: Implement GET /api/student/question-type-performance
- **File:** `backend/app/routers/student.py`
- **Effort:** 1 day
- **Dependency:** TASK-006 (pattern established)
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Create QuestionTypePerformanceResponse model
  - **Fields:** by_question_type, easiest_types, hardest_types
  - **Criteria:** Response model ready

- [ ] Query Question.stem_type_key + accuracy by type
  - **Query:** JOIN Question → stem_type_key, aggregate accuracy
  - **Criteria:** Query works

- [ ] Implement endpoint
  - **Endpoint:** GET /api/student/question-type-performance
  - **Criteria:** Accessible

- [ ] Write basic tests
  - **File:** `backend/tests/test_question_type_performance.py`
  - **Criteria:** Tests pass

**Acceptance Criteria:**
- ✅ Endpoint returns question type breakdown
- ✅ Accuracy per type correct
- ✅ Tests pass

---

#### TASK-009: Implement GET /api/student/trap-details/{trap_type}
- **File:** `backend/app/routers/student.py`
- **Effort:** 0.5 days
- **Dependency:** TASK-008 (endpoint pattern)
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Create TrapDetailResponse model
  - **Fields:** trap_type, definition, your_stats, example_mistakes, learning_resources
  - **Criteria:** Model complete

- [ ] Implement endpoint
  - **Route:** GET /api/student/trap-details/{trap_type}
  - **Logic:** Filter UserProgress by user_id + trap_type, get examples
  - **Criteria:** Works

- [ ] Write tests
  - **Criteria:** Tests pass

**Acceptance Criteria:**
- ✅ Endpoint returns trap details
- ✅ Includes user statistics
- ✅ Includes example questions

---

## TIER 3: Frontend Dashboard (Days 8-10)

### 🟢 Dashboard Component

#### TASK-010: Create StudentTrapSusceptibilityDashboard Component
- **File:** `APP/STUDENT_APP_REDUX/src/components/StudentTrapSusceptibilityDashboard.tsx` (new file)
- **Effort:** 1.5 days
- **Dependency:** TASK-006 (API ready)
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Create component boilerplate
  - **Import:** React hooks, API client, types
  - **Criteria:** Component structure ready

- [ ] Call GET /api/student/trap-susceptibility
  - **Hook:** useQuery from react-query
  - **Criteria:** Data fetches on mount

- [ ] Display trap fall rates as pie chart
  - **Library:** Recharts or similar
  - **Data:** most_susceptible_traps
  - **Criteria:** Chart renders

- [ ] Add severity color coding
  - **Critical (>0.80):** Red
  - **High (0.60-0.80):** Orange
  - **Moderate (0.40-0.60):** Yellow
  - **Low (<0.40):** Green
  - **Criteria:** Colors applied

- [ ] Create clickable trap cards
  - **Card:** Shows trap_type, fall_rate, occurrences
  - **Click:** Navigates to trap-details view
  - **Criteria:** Cards interactive

- [ ] Display improvement indicators
  - **Show:** overcoming_traps (green checkmark + % improvement)
  - **Show:** persistent_traps (red warning + %still struggling)
  - **Criteria:** Indicators visible

- [ ] Add loading/error states
  - **Loading:** Skeleton loader
  - **Error:** Error message with retry button
  - **Criteria:** States handled

- [ ] Test component rendering
  - **Tool:** React Testing Library
  - **Criteria:** Component renders without errors

**Acceptance Criteria:**
- ✅ Component renders all trap data
- ✅ Colors match severity
- ✅ Charts display correctly
- ✅ Links to detail view work
- ✅ Loading/error states work

---

#### TASK-011: Create TrapDetailView Component
- **File:** `APP/STUDENT_APP_REDUX/src/components/TrapDetailView.tsx` (new file)
- **Effort:** 1.5 days
- **Dependency:** TASK-009 (API ready)
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Create component for detailed trap breakdown
  - **Route:** `/traps/{trap_type}` or similar
  - **Criteria:** Component structure ready

- [ ] Call GET /api/student/trap-details/{trap_type}
  - **Criteria:** Data fetches

- [ ] Display trap definition
  - **Section:** "What is this trap?"
  - **Content:** Definition + why it's effective
  - **Criteria:** Renders

- [ ] Show student's statistics on this trap
  - **Section:** "Your Performance"
  - **Data:** times_encountered, times_fell_for, fall_rate, recent_accuracy
  - **Criteria:** Stats displayed

- [ ] Display example questions with this trap
  - **Section:** "Example Questions"
  - **Content:** Question text, correct answer, student's answer, explanation
  - **Criteria:** Examples show

- [ ] Show improvement trend chart
  - **Chart:** Line graph of first 5 attempts vs recent 5 attempts
  - **Criteria:** Chart renders

- [ ] Add "Practice This Trap" button
  - **Action:** Creates study session with this trap type
  - **Criteria:** Button functional

- [ ] Write tests
  - **Criteria:** Tests pass

**Acceptance Criteria:**
- ✅ Component displays all trap details
- ✅ Shows examples accurately
- ✅ Trend chart is correct
- ✅ "Practice" button works
- ✅ Tests pass

---

#### TASK-012: Update Dashboard Navigation
- **File:** `APP/STUDENT_APP_REDUX/src/pages/DashboardPage.tsx`
- **Effort:** 0.5 days
- **Dependency:** TASK-010, TASK-011
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Add "Your Traps" section to dashboard
  - **Location:** Below "Recommendations"
  - **Content:** StudentTrapSusceptibilityDashboard component
  - **Criteria:** Section visible on dashboard

- [ ] Add link to trap detail view from dashboard card
  - **Click:** Trap card → navigate to TrapDetailView
  - **Criteria:** Navigation works

- [ ] Test dashboard still works
  - **Manual Test:** Load dashboard, verify no errors
  - **Criteria:** Dashboard functional

**Acceptance Criteria:**
- ✅ Dashboard shows trap susceptibility section
- ✅ Links to detail views work
- ✅ No regressions in existing dashboard features

---

### 🔵 Integration Testing

#### TASK-013: End-to-End Dashboard Test
- **Effort:** 1 day
- **Dependency:** TASK-010, TASK-011, TASK-012
- **Status:** ☐ Not Started

**Subtasks:**
- [ ] Load dashboard
  - **Step:** Navigate to `/`
  - **Criteria:** Dashboard loads

- [ ] Verify trap susceptibility section appears
  - **Check:** StudentTrapSusceptibilityDashboard visible
  - **Criteria:** Component rendered

- [ ] Verify pie chart shows trap data
  - **Check:** Chart has data points for each trap
  - **Criteria:** Chart populated

- [ ] Click on trap card
  - **Action:** Click "subject_number_mismatch" card
  - **Expected:** Navigate to detail view
  - **Criteria:** Navigation works

- [ ] Verify detail view loads
  - **Check:** Trap definition visible
  - **Check:** Student statistics visible
  - **Check:** Example questions visible
  - **Criteria:** All sections render

- [ ] Click "Practice This Trap"
  - **Expected:** Creates study session
  - **Criteria:** Action works

- [ ] Test with different users
  - **Setup:** Create 2 test users with different trap patterns
  - **Verify:** Each sees correct data
  - **Criteria:** Data isolation works

- [ ] Verify no console errors
  - **Tool:** Browser DevTools
  - **Criteria:** No errors/warnings

**Acceptance Criteria:**
- ✅ Dashboard displays trap data
- ✅ Navigation between views works
- ✅ Detail view shows accurate information
- ✅ Data is isolated per user
- ✅ No console errors
- ✅ All components render properly

---

## TIER 4: Optimization & Integration (Days 11-14)

### 🟡 Database Optimization (Optional)

#### TASK-014: Create StudentTrapSusceptibility Table
- **File:** `backend/alembic/versions/XXX_add_student_trap_susceptibility.py` (new migration)
- **Effort:** 1 day
- **Dependency:** None (can do anytime after TASK-006)
- **Status:** ❌ Declined 2026-07-05 — see decision note below

**Decision (2026-07-05):** Declined as a nightly-batch job. The nightly design means the dashboard shows yesterday's trap stats, not today's — a student's most recent answers wouldn't appear until the next day's job ran. User rejected that staleness tradeoff. Current traffic is essentially one test user, so there is no performance problem the live query needs solving yet. `GET /api/student/trap-susceptibility` stays as a live on-the-fly aggregation from `user_progress`. **Moved to `future_features.md` → "Student Tracking — Trap Analysis (Phase 2.5 leftovers)"** to revisit when server load makes it measurably slow — and when it's revisited, prefer a write-through cache or short-TTL read cache over a nightly batch. Full decision rationale also in `.wolf/cerebrum.md` Decision Log (2026-07-05).

---

#### TASK-015: Backfill Historical Trap Data
- **Effort:** 0.5 days
- **Dependency:** standalone
- **Status:** Being handled on a separate data-integrity branch (owner: user), alongside chart/graph fill issues — not tracked further in this file.

---

### 🟢 Cross-Phase Integration

#### TASK-016: Integrate with Phase 2 (Spaced Repetition)
- **Status:** Blocked by Phase 2 (Spaced Repetition). **Moved to `future_features.md` → "Student Tracking — Trap Analysis (Phase 2.5 leftovers)"**.

---

#### TASK-017: Integrate with Phase 3 (Analytics)
- **Status:** Blocked by Phase 3 (Analytics). **Moved to `future_features.md` → "Student Tracking — Trap Analysis (Phase 2.5 leftovers)"**.
- ✅ Frontend displays trends correctly

---

## SUMMARY TABLE

| Task ID | Task Name | Effort | Dependency | Status |
|---------|-----------|--------|------------|--------|
| TASK-001 | Extract trap in useGrammarSession | 1d | None | ✅ |
| TASK-002 | Extract trap in DiagnosticTab | 0.5d | 001 | ✅ |
| TASK-003 | Update API client types | 0.5d | 001,002 | ✅ |
| TASK-004 | Backend type updates | 0.5d | None | ✅ (pre-existing) |
| **TASK-005** | **Manual integration test** | **1d** | **001-004** | **✅ (fully verified 2026-07-05: API, DB, and live manual browser click-through)** |
| TASK-006 | GET /api/student/trap-susceptibility | 1.5d | 005 | ✅ |
| TASK-007 | Test trap susceptibility endpoint | 1d | 006 | ✅ |
| TASK-008 | GET question-type-performance | 1d | 006 | ✅ |
| TASK-009 | GET trap-details/{trap_type} | 0.5d | 008 | ✅ |
| TASK-010 | TrapSusceptibilityDashboard component | 1.5d | 006 | ✅ |
| TASK-011 | TrapDetailView component | 1.5d | 009 | ✅ |
| TASK-012 | Update dashboard navigation | 0.5d | 010,011 | ✅ |
| **TASK-013** | **End-to-end dashboard test** | **1d** | **010-012** | **✅** |
| TASK-014 | Create StudentTrapSusceptibility table (OPT) | 1d | 006 | ❌ Declined 2026-07-05 (nightly staleness rejected; live query kept) |
| TASK-015 | Backfill historical trap data (OPT) | 0.5d | standalone | ☐ |
| TASK-016 | Integrate with Phase 2 (Blocked) | 1d | Phase 2 | ☐ |
| TASK-017 | Integrate with Phase 3 (Blocked) | 0.5d | Phase 3 | ☐ |

---

## Critical Path

```
TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005 (Verification)
                                                    ↓
                                          TASK-006 → TASK-007
                                             ↓          ↓
                                    TASK-008, TASK-010, TASK-009
                                             ↓
                                          TASK-011
                                             ↓
                                          TASK-012
                                             ↓
                                          TASK-013 (Verification)
```

**Critical Path Duration:** ~10 days (Tier 1-3)  
**Optional Optimization:** +2 days (Tier 4.1)  
**Cross-Phase Integration:** +1.5 days (Tier 4.2, blocked by Phase 2/3)

---

## Daily Schedule (Recommended)

### Week 1: Frontend + Foundation

**Day 1 (Mon):**
- TASK-001: Extract trap in useGrammarSession (1d)

**Day 2 (Tue):**
- TASK-002: Extract trap in DiagnosticTab (0.5d)
- TASK-003: Update API client types (0.5d)
- TASK-004: Backend type updates (0.5d)
- *Parallel*: Code review of changes

**Day 3 (Wed):**
- TASK-005: Manual integration test (1d)
- Verify data flowing end-to-end

**Day 4 (Thu):**
- TASK-006: GET /api/student/trap-susceptibility (1.5d)
- *Start*: TASK-007 test writing

### Week 2: Backend APIs + Frontend

**Day 5 (Fri):**
- TASK-006 continued (0.5d)
- TASK-007: Test endpoint (0.5d)
- TASK-008: GET question-type-performance (1d)

**Day 6 (Mon):**
- TASK-008 continued (1d)
- TASK-009: GET trap-details (0.5d)

**Day 7 (Tue):**
- TASK-010: TrapSusceptibilityDashboard (1.5d)

**Day 8 (Wed):**
- TASK-010 continued (0.5d)
- TASK-011: TrapDetailView (1.5d)

**Day 9 (Thu):**
- TASK-011 continued (0.5d)
- TASK-012: Update dashboard (0.5d)
- TASK-013: E2E dashboard test (0.5d)

**Day 10 (Fri):**
- TASK-013 continued (0.5d)
- Buffer for fixes/issues
- Documentation review

### Week 3 (Optional): Optimization

**Day 11 (Mon):**
- TASK-014: StudentTrapSusceptibility table (1d)

**Day 12 (Tue):**
- TASK-015: Backfill historical data (0.5d)
- Testing + verification (0.5d)

**Day 13-14:**
- TASK-016/017: Cross-phase integration (when Phase 2/3 ready)

---

## Success Metrics

✅ **Code Quality:**
- [ ] All new code has test coverage >= 90%
- [ ] TypeScript compiles without errors
- [ ] ESLint passes in frontend
- [ ] No console errors/warnings

✅ **Data Accuracy:**
- [ ] Fall rates match manual SQL verification
- [ ] Trap types correctly extracted from options
- [ ] Both focus_key and trap_key populated for all answers

✅ **Performance:**
- [ ] Trap susceptibility query < 200ms
- [ ] Dashboard components load in < 1s
- [ ] No N+1 queries

✅ **UX:**
- [ ] All links navigate correctly
- [ ] Loading/error states work
- [ ] Data is isolated per user
- [ ] No regressions in existing features

✅ **Documentation:**
- [ ] API endpoints documented
- [ ] Component props documented
- [ ] Database migration documented

---

## Notes & Caveats

- **TASK-005** is a critical checkpoint — if data doesn't flow end-to-end, everything after is blocked.
- **TASK-013** is a second critical checkpoint — verifies all UI works correctly before optimization.
- **TASK-014/015** are optional optimizations for production performance — can be deferred to later if needed.
- **TASK-016/017** depend on Phase 2 and Phase 3 being available — schedule after those phases complete.
- All timestamps assume 8-hour work days and no major blockers.
- Buffer 20-30% time for testing, debugging, and unexpected issues.

---

## Related Documentation

- Implementation Audit: `STUDENT_TRACKING_AUDIT.md`
- Full PRD: `student_tracking_backend_prd.md`
- Database Schema: `backend/app/models/db.py`
- API Routes: `backend/app/routers/student.py`
- Frontend Components: `APP/STUDENT_APP_REDUX/src/components/`
