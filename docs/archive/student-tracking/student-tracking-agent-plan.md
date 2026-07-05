# Student Tracking — Serial Execution with Subagents

**Strategy:** Sequential task execution (10 days) with specialized agents for each domain.

**Agent Assignments:**
- **frontend-developer** — All React/TypeScript work
- **backend-architect** — All Python/FastAPI work  
- **test-writer-fixer** — Integration testing + validation

**Handoff Pattern:** Frontend → Backend → QA → Frontend → QA

---

## TIER 1: Frontend Data Flow (Days 1-4)

### Day 1: Extract Trap Type in Frontend
**Agent: frontend-developer**  
**Task:** TASK-001 + TASK-002 + TASK-003

**Objective:** Get trap type data flowing from frontend to backend API

**Subtasks:**
1. Extract trap type in `useGrammarSession.ts`
   - Find selected option, extract `distractor_type_key`
   - Pass `missed_syntactic_trap_key` to `/api/submit`
   
2. Extract trap type in `DiagnosticTab.tsx`
   - Same pattern: extract from selected option
   - Pass in submission

3. Update API client types
   - Add `missed_syntactic_trap_key?: string` to submitAnswer params

**Success:** Network requests include trap data

**Handoff:** → Backend Agent (ready for TASK-004)

---

### Day 2: Backend Type Layer
**Agent: backend-architect**  
**Task:** TASK-004

**Objective:** Verify backend accepts and stores trap data

**Subtasks:**
1. Verify UserProgressCreate has field
2. Verify submit_answer endpoint stores it
3. Check UserProgress table has column

**Success:** Backend receives and stores trap_key in DB

**Handoff:** → QA Agent (ready for TASK-005)

---

### Days 3-4: Integration Verification
**Agent: test-writer-fixer**  
**Task:** TASK-005

**Objective:** Verify end-to-end data flow works

**Subtasks:**
1. Start dev stack
2. Create test user
3. Answer grammar question
4. Check network request has trap data
5. Check database has stored trap
6. Run diagnostic session
7. Verify all answers have trap data

**Success:** Both focus_key and trap_key populated for all answers  
**Blocker Release:** ✅ UNLOCK TIER 2

**Handoff:** → Backend Agent (ready for TASK-006)

---

## TIER 2: Backend Analytics (Days 5-7)

### Day 5: Core Analytics Endpoint
**Agent: backend-architect**  
**Task:** TASK-006 + TASK-007

**Objective:** Build trap susceptibility API

**Subtasks:**
1. Create StudentTrapSusceptibilityResponse model
2. Write SQL query to aggregate UserProgress by trap
3. Calculate fall_rate = 1 - (correct / total)
4. Identify top 5 susceptible traps
5. Calculate improvement trends (first 5 vs last 5 attempts)
6. Implement GET /api/student/trap-susceptibility endpoint
7. Add error handling
8. Write pytest tests for endpoint
9. Verify fall rates match manual SQL

**Success:** Endpoint returns accurate trap data < 200ms

**Handoff:** → Backend continues (TASK-008/009 same day)

---

### Day 6: Additional Endpoints
**Agent: backend-architect**  
**Task:** TASK-008 + TASK-009

**Objective:** Build question type + trap detail endpoints

**Subtasks:**
1. GET /api/student/question-type-performance
   - Query by stem_type_key
   - Calculate accuracy per type
   
2. GET /api/student/trap-details/{trap_type}
   - Return definition, user stats, examples

**Success:** Both endpoints working with tests

**Handoff:** → Frontend Agent (ready for TASK-010/011)

---

## TIER 3: Frontend Dashboard (Days 7-10)

### Day 7: Trap Dashboard Component
**Agent: frontend-developer**  
**Task:** TASK-010

**Objective:** Display trap susceptibility data

**Subtasks:**
1. Create StudentTrapSusceptibilityDashboard.tsx
2. Call GET /api/student/trap-susceptibility
3. Render trap fall rates as pie chart
4. Add severity color coding (red/orange/yellow/green)
5. Create clickable trap cards
6. Show improvement indicators
7. Add loading/error states
8. Test component rendering

**Success:** Dashboard renders trap data with colors and interactions

**Handoff:** → Frontend continues (TASK-011 parallel task)

---

### Day 8: Detail View Component
**Agent: frontend-developer**  
**Task:** TASK-011

**Objective:** Display trap details on click

**Subtasks:**
1. Create TrapDetailView.tsx
2. Call GET /api/student/trap-details/{trap_type}
3. Display trap definition
4. Show student's stats on this trap
5. Display example questions with explanations
6. Render improvement trend chart
7. Add "Practice This Trap" button
8. Test component

**Success:** Detail view shows all information correctly

**Handoff:** → Frontend continues (TASK-012)

---

### Day 9: Dashboard Integration
**Agent: frontend-developer**  
**Task:** TASK-012

**Objective:** Wire components together

**Subtasks:**
1. Add "Your Traps" section to main dashboard
2. Add link from trap card to detail view
3. Make detail view a routable page
4. Test all navigation works
5. Verify no dashboard regressions

**Success:** Dashboard integrated and navigable

**Handoff:** → QA Agent (ready for TASK-013)

---

### Days 9-10: End-to-End Validation
**Agent: test-writer-fixer**  
**Task:** TASK-013

**Objective:** Verify entire system works together

**Subtasks:**
1. Load dashboard
2. Verify trap section appears
3. Check pie chart has data
4. Click trap card → navigate to detail
5. Verify detail view loads completely
6. Click "Practice This Trap"
7. Test with different users
8. Verify no console errors
9. Check data isolation per user

**Success:** Complete feature works end-to-end  
**Blocker Release:** ✅ PHASE 2.5 MVP COMPLETE

**Handoff:** → Backend Agent (optional TASK-014/015)

---

## TIER 4: Optional Optimization (Days 11-12)

### Day 11: Database Optimization
**Agent: backend-architect**  
**Task:** TASK-014 + TASK-015

**Objective:** Create StudentTrapSusceptibility table + backfill (optional)

**Subtasks:**
1. Create Alembic migration
2. Add StudentTrapSusceptibility table
3. Add to SQLAlchemy models
4. Write nightly aggregation job
5. Schedule with APScheduler
6. Update endpoint to use new table
7. Verify query performance < 50ms
8. Write backfill script
9. Test on staging data
10. Run backfill

**Success:** Dashboard queries drop from 2s to < 50ms

**Handoff:** → Backend continues (TASK-016/017 if Phase 2/3 ready)

---

## AGENT COMMUNICATION PROTOCOL

### Hand-off Checklist (Each Agent Must Verify)

**When Starting a Task:**
- [ ] Read previous task's "Success" criteria
- [ ] Verify prerequisites are complete
- [ ] Run related tests to confirm
- [ ] Start with clean git status

**When Completing a Task:**
- [ ] Run tests (pytest for backend, React testing for frontend)
- [ ] Verify no console errors
- [ ] Document any issues in Git commit message
- [ ] Create Git commit with task ID (e.g., "feat: implement TASK-006")
- [ ] Push to origin before handing off

**Blocked Handoff:**
- If task fails TASK-005 or TASK-013, STOP and investigate
- Do not proceed to next tier until checkpoint passes
- Document blocker in commit message

---

## Serial Execution Schedule

```
Week 1:
  Mon (Day 1):   frontend-developer → TASK-001/002/003
  Tue (Day 2):   backend-architect → TASK-004
  Wed (Day 3-4): test-writer-fixer → TASK-005 (CRITICAL CHECKPOINT ✅)

Week 2:
  Thu (Day 5):   backend-architect → TASK-006/007
  Fri (Day 6):   backend-architect → TASK-008/009
  Mon (Day 7):   frontend-developer → TASK-010
  Tue (Day 8):   frontend-developer → TASK-011
  Wed (Day 9):   frontend-developer → TASK-012
  Thu (Day 9-10): test-writer-fixer → TASK-013 (CRITICAL CHECKPOINT ✅)

Week 3 (Optional):
  Fri (Day 11-12): backend-architect → TASK-014/015
```

---

## Commit Message Format per Agent

**Frontend tasks:**
```
feat(TASK-XXX): [feature name]

- Extracted trap type from selected option
- Pass missed_syntactic_trap_key to /api/submit
- Updated API client types
- Tested with grammar practice questions

Related task: TASK-001, TASK-002, TASK-003
```

**Backend tasks:**
```
feat(TASK-XXX): [feature name]

- Implemented GET /api/student/trap-susceptibility
- Added StudentTrapSusceptibilityResponse model
- Wrote pytest tests (90%+ coverage)
- Verified fall rate calculations

Related task: TASK-006, TASK-007
```

**QA/Integration tasks:**
```
test(TASK-XXX): [integration test name]

Manual integration test results:
✅ Data flows end-to-end
✅ Frontend sends trap data in network request
✅ Backend stores trap data in DB
✅ Dashboard displays trap data correctly
✅ No console errors or regressions

Checkpoint: TASK-005 complete
Checkpoint: TASK-013 complete
```

---

## Key Decision Points

**Q: What if TASK-005 fails?**  
A: STOP. Do not proceed to TASK-006. Diagnose the data flow issue:
   - Check frontend network request (has trap_key?)
   - Check backend receives it (logs)
   - Check database (is column populated?)
   
   Re-run TASK-001/004 if needed.

**Q: What if TASK-013 fails?**  
A: STOP. Do not release. Diagnose:
   - Does dashboard load?
   - Do components render?
   - Is data correct?
   
   Re-run TASK-010/011/012 as needed.

**Q: Can TIER 4 be skipped?**  
A: YES. TIER 4 is optional optimization. MVP works without it.
   Only do TIER 4 if:
   - Dashboard queries are slow (> 500ms)
   - User feedback indicates performance issues
   - You want <50ms query times

**Q: When do cross-phase integrations (TASK-016/017) start?**  
A: Only after Phase 2 and Phase 3 are complete.
   - TASK-016 integrates with Phase 2 (Spaced Repetition)
   - TASK-017 integrates with Phase 3 (Analytics)
   
   Don't start these until those phases are in production.

---

## Success Definition: MVP Complete

✅ **Data Layer:**
- Frontend extracts trap type from selected option
- Backend receives and stores `missed_syntactic_trap_key`
- Database has populated trap data for all answers

✅ **Analytics Layer:**
- GET /api/student/trap-susceptibility returns accurate fall rates
- Endpoint responds < 200ms
- 95%+ accuracy vs manual SQL verification

✅ **UI Layer:**
- Dashboard shows trap susceptibility data
- Trap cards are clickable
- Detail view explains each trap
- Navigation works end-to-end

✅ **Quality:**
- All tests pass (pytest + React Testing Library)
- No console errors
- No regressions in existing features

✅ **Documentation:**
- All tasks committed with clear messages
- Code has inline comments for complex logic
- API endpoints have docstrings

---

## Resources per Agent

### frontend-developer needs:
- `APP/STUDENT_APP_REDUX/src/` directory structure
- Line numbers from student-tracking-tasks.md (TASK-001-003, 010-013)
- API endpoint specs from STUDENT_TRACKING_AUDIT.md
- React Testing Library for component tests

### backend-architect needs:
- `backend/app/routers/student.py` for endpoint implementation
- `backend/app/models/payload.py` for response models
- `backend/app/models/db.py` for table schema
- pytest for endpoint testing
- SQL knowledge for aggregation queries

### test-writer-fixer needs:
- Browser DevTools access (Network, Console tabs)
- SQL client access (psql or similar)
- pytest test runner
- React Testing Library setup
- Dev stack running (PostgreSQL + backend + frontend)

---

## Quick Start for Agent

**Copy this prompt for each agent:**

> **Task:** Implement TASK-XXX
>
> **Context:** See `/home/jb/DSAT_REDUX_MD/student-tracking-tasks.md` for full task details
> 
> **Agent Type:** [frontend-developer | backend-architect | test-writer-fixer]
>
> **Files to modify:**
> - [List from tasks.md]
>
> **Success criteria:**
> - [From tasks.md]
>
> **After complete:**
> 1. Run tests
> 2. Create git commit with format from `student-tracking-agent-plan.md`
> 3. Push to origin
> 4. Report completion

---

## Progress Tracking

Use this checklist to track completion:

- [ ] TASK-001 (frontend-developer) ✅ Day 1
- [ ] TASK-002 (frontend-developer) ✅ Day 1
- [ ] TASK-003 (frontend-developer) ✅ Day 1
- [ ] TASK-004 (backend-architect) ✅ Day 2
- [ ] TASK-005 (test-writer-fixer) ✅ Day 3-4 **CHECKPOINT**
- [ ] TASK-006 (backend-architect) ✅ Day 5
- [ ] TASK-007 (backend-architect) ✅ Day 5
- [ ] TASK-008 (backend-architect) ✅ Day 6
- [ ] TASK-009 (backend-architect) ✅ Day 6
- [ ] TASK-010 (frontend-developer) ✅ Day 7
- [ ] TASK-011 (frontend-developer) ✅ Day 8
- [ ] TASK-012 (frontend-developer) ✅ Day 9
- [ ] TASK-013 (test-writer-fixer) ✅ Day 9-10 **CHECKPOINT**
- [ ] TASK-014 (backend-architect) ☐ Day 11 (OPTIONAL)
- [ ] TASK-015 (backend-architect) ☐ Day 12 (OPTIONAL)
- [ ] TASK-016 (backend-architect) ☐ BLOCKED until Phase 2
- [ ] TASK-017 (backend-architect) ☐ BLOCKED until Phase 3

---

**Status:** Ready for agent execution. Each agent should follow their domain tasks in sequence, verify hand-off conditions, and commit after completion.
