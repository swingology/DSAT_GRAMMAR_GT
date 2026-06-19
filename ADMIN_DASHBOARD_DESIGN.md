# DSAT Admin Dashboard — Design & Implementation Plan

**Status:** Design (v1.0)  
**Date:** 2026-06-18  
**Target:** React/Vite + FastAPI backend  
**Scope:** Question management, review queue, analytics, bulk operations

---

## 1. Executive Summary

The DSAT Admin Dashboard is a web-based interface for managing official and generated grammar practice questions at scale. Built on the existing FastAPI backend and React frontend patterns, it serves three core admin workflows:

1. **Question Management** — View/edit/create questions with full annotations
2. **Review & Approval** — Ingest pipeline queue with approve/reject/comment workflow
3. **Analytics & Bulk Operations** — Performance metrics, trap effectiveness, bulk re-annotation

**Initial Scope (MVP):** Question list + detail view with edit capabilities, simple approval queue.

---

## 2. System Architecture

### 2.1 Tech Stack
- **Frontend:** React 18 + TypeScript + Vite (extends existing `/FRONTEND`)
- **Backend:** FastAPI (existing `/backend/app/routers/admin.py`)
- **Database:** PostgreSQL (existing)
- **Styling:** Tailwind CSS (matches `grammar-app.html` palette)
- **State:** React Query (TanStack) for API caching
- **Forms:** React Hook Form + Zod validation

### 2.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN DASHBOARD (React)                      │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Question     │  │ Review       │  │ Analytics    │          │
│  │ Manager      │  │ Queue        │  │ & Bulk Ops   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                 │
└─────────┼─────────────────┼──────────────────┼─────────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
    ┌──────────────────────────────────────────────────┐
    │       FastAPI Routes (backend/app/routers)       │
    │                                                  │
    │  • admin.py — existing admin endpoints          │
    │  • admin-questions.py — new Q mgmt routes       │
    │  • admin-review.py — new approval queue routes  │
    │  • admin-analytics.py — new analytics routes    │
    └──────────┬───────────────────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────────────────┐
    │    PostgreSQL (Question, Annotation, Job, etc)   │
    │    (Existing models in backend/app/models/db.py) │
    └──────────────────────────────────────────────────┘
```

### 2.3 Authentication & Authorization

- **Mechanism:** JWT-based (reuse existing `app.auth.admin_required` decorator)
- **Admin Check:** All admin routes require `admin_required` dependency
- **Session:** Cookie-based or Authorization header (match grammar-app.html pattern)

---

## 3. Feature Breakdown

### 3.1 Question Management

#### List View
- **Display:** Paginated table (25 rows/page) with sorting & filtering
- **Columns:**
  - Question ID (link to detail)
  - Source info (test name, question number)
  - Content origin (official/generated)
  - Status (draft/approved/rejected)
  - Answers correct (% correct from user progress)
  - Last modified (date)
- **Filters:**
  - Status (draft, approved, rejected)
  - Origin (official, generated)
  - Test (dropdown, auto-populated)
  - Focus key (grammar/reading)
  - Date range

#### Detail View
- **Question Display:**
  - Question text (editable)
  - Passage/paired passage (if applicable)
  - Current options A-D (editable)
  - Correct answer indicator
  - Explanation (editable)

- **Annotation Panel (Read-Only/View):**
  - Grammar focus keys (from `question_annotations.annotation_jsonb`)
  - Trap keys (from `annotation_jsonb.trap_keys`)
  - Syntactic traps (from `annotation_jsonb.syntactic_traps`)
  - Distractor analysis per option
  - Confidence scores

- **Actions:**
  - Save (POST to `/admin/questions/{id}/edit`)
  - Mark as needs review
  - Approve/reject
  - Create new version (change log)

#### Create/Edit Modal
- Form fields:
  - Question text (rich text editor or textarea)
  - Passage text (optional)
  - Options A-D
  - Correct answer
  - Explanation
  - Metadata: test name, question number, etc.
- **Validation:**
  - Exactly one correct option
  - Non-empty question text
  - At least 4 options (A-D)

### 3.2 Review & Approval Queue

#### Queue View
- **Status:** Questions pending review from ingestion pipeline
- **Display:** List of jobs with:
  - Job ID
  - Question count
  - Job status (pending, in_progress, needs_review, approved, failed)
  - Error summary (if any)
  - Triggered at (date/time)
  - Actions: Review, Reject All, Approve All

#### Job Detail View
- **Summary:**
  - Job metadata (type, provider, model, rules version)
  - Question count vs. expected
  - Validation issues (if any)
  
- **Question List (within job):**
  - Quick inline preview
  - Issue badge (warning icon if qnum mismatch, etc.)
  - Action: Approve individual, Reject with reason
  
- **Approve/Reject Workflow:**
  - Approve: Updates `practice_status = "approved"`, marks job as `approved`
  - Reject: Sets `practice_status = "rejected"`, prompts for reason
  - Comment: Add admin notes to `AdminQuestionAuditLog`

### 3.3 Analytics Dashboard

#### Performance Metrics
- **By Focus Key:**
  - % correct (overall + by difficulty)
  - Student count
  - Attempt count
  - Struggle points (questions with <40% correct)
  
- **Trap Effectiveness:**
  - Per trap key, % of students who select each distractor
  - Most effective traps (highest distractor selection)
  - Least effective traps (too easy to spot)

#### Question Quality Metrics
- **Coverage:**
  - Questions per focus key
  - Tests with full coverage vs. gaps
  - Module coverage (SEC 1/2 for grammar)

- **Data Anomalies:**
  - Questions with no user attempts
  - Questions with missing annotations
  - Duplicate questions (high similarity)

### 3.4 Bulk Operations

#### Re-Annotation
- **Trigger:** Button to re-run annotation pipeline on selected questions
- **Batch:** Up to 50 questions
- **Tracking:** Job ID, progress bar
- **Webhook:** Background task, admin notified when complete

#### Trap Configuration
- **List:** All trap keys in use
- **Edit:** Modify trap parameters (e.g., effectiveness threshold)
- **Add:** Create new syntactic trap
- **Delete:** Archive unused traps

#### Bulk Grammar Key Updates
- **Search:** Questions matching a criterion (e.g., all "verb_form" focus)
- **Bulk Update:** Change focus key across multiple questions
- **Audit:** Log change with user, timestamp, count affected

---

## 4. Database & API

### 4.1 Existing Models (backend/app/models/db.py)

```python
# Core models for admin dashboard:

Question
  - id, content_origin, practice_status
  - current_question_text, current_passage_text
  - current_correct_option_label, current_explanation_text
  - latest_annotation_id, latest_version_id
  - source_test_name, source_question_number
  - created_at, updated_at

QuestionAnnotation
  - id, question_id, annotation_jsonb, explanation_jsonb
  - rules_version, prompt_version, confidence_jsonb

QuestionOption
  - id, question_id, option_label, option_text, is_correct
  - distractor_type_key, why_plausible, why_wrong

QuestionVersion
  - id, question_id, version_number, change_source
  - question_text, choices_jsonb, correct_option_label
  - editor_user_id, change_notes

QuestionJob
  - id, job_type, status, content_origin
  - question_id, validation_errors_jsonb
  - created_at, updated_at

AdminQuestionAuditLog
  - id, question_id, admin_user_id, action, notes, created_at
```

### 4.2 API Endpoints

#### Question Management
```
GET    /admin/questions
       Query: page=1, limit=25, status=, origin=, test=, date_from=, date_to=
       Returns: {questions: [...], total: 150, page: 1}

GET    /admin/questions/{question_id}
       Returns: Full question + annotation + options + versions

POST   /admin/questions/{question_id}/edit
       Body: {question_text, passage_text, options: [{label, text, is_correct}], explanation_text, notes}
       Returns: Updated question

POST   /admin/questions
       Body: {content_origin, question_text, passage_text, options, ...}
       Returns: Created question

DELETE /admin/questions/{question_id}
       Returns: {ok: true}
```

#### Review & Approval
```
GET    /admin/jobs
       Query: status=needs_review, page=1, limit=25
       Returns: Jobs awaiting review

GET    /admin/jobs/{job_id}
       Returns: Job + embedded questions (first 20)

GET    /admin/jobs/{job_id}/questions
       Query: page=1, limit=25
       Returns: Paginated questions in job

POST   /admin/jobs/{job_id}/questions/{question_id}/approve
       Returns: {ok: true}

POST   /admin/jobs/{job_id}/questions/{question_id}/reject
       Body: {reason: "..."}
       Returns: {ok: true}

POST   /admin/jobs/{job_id}/approve
       Body: Optional notes
       Returns: {ok: true, approved_count: N}

POST   /admin/jobs/{job_id}/reject
       Body: {reason: "..."}
       Returns: {ok: true}
```

#### Analytics
```
GET    /admin/analytics/performance
       Query: focus_key=, date_from=, date_to=
       Returns: {by_focus_key: [...], overall: {...}}

GET    /admin/analytics/traps
       Query: focus_key=, limit=20
       Returns: {trap_effectiveness: [...]}

GET    /admin/analytics/coverage
       Returns: {coverage_by_key: {...}, gap_report: [...]}
```

#### Bulk Operations
```
POST   /admin/bulk/reannotate
       Body: {question_ids: [...]}
       Returns: {job_id, questions_queued: N}

POST   /admin/bulk/update-focus-key
       Body: {question_ids: [...], old_key: "...", new_key: "..."}
       Returns: {updated: N}

GET    /admin/bulk/job/{job_id}
       Returns: {status, progress: N/total}
```

---

## 5. Component Architecture

### 5.1 Directory Structure

```
FRONTEND/src/
├── pages/
│   ├── AdminDashboard.tsx         ← Root layout (sidenav + content)
│   ├── QuestionListPage.tsx       ← Question table
│   ├── QuestionDetailPage.tsx     ← Detail view + edit
│   ├── ReviewQueuePage.tsx        ← Approval queue
│   ├── AnalyticsPage.tsx          ← Metrics dashboard
│   └── BulkOpsPage.tsx            ← Bulk operations
│
├── components/admin/
│   ├── QuestionTable.tsx          ← Sortable/filterable table
│   ├── QuestionForm.tsx           ← Create/edit form
│   ├── AnnotationPanel.tsx        ← Read-only annotation display
│   ├── ReviewQueue.tsx            ← Job + inline Q preview
│   ├── AnalyticsCard.tsx          ← Metric card (reusable)
│   ├── ApprovalModal.tsx          ← Approve/reject dialog
│   └── BulkOperationStatus.tsx    ← Job progress tracker
│
├── hooks/
│   ├── useQuestions.ts            ← React Query hooks
│   ├── useJobs.ts
│   ├── useAnalytics.ts
│   └── useBulkOps.ts
│
├── api/admin/
│   ├── questions.ts               ← API client functions
│   ├── jobs.ts
│   ├── analytics.ts
│   └── bulkOps.ts
│
├── types/admin.ts                 ← TypeScript interfaces
└── styles/admin.css               ← Admin-specific styles (Tailwind)
```

### 5.2 Key Components

#### QuestionTable.tsx
```typescript
interface QuestionTableProps {
  data: Question[];
  loading: boolean;
  page: number;
  total: number;
  onPageChange: (page: number) => void;
  onSort: (field: string, dir: 'asc' | 'desc') => void;
  onSelectQuestion: (id: string) => void;
}

export const QuestionTable: React.FC<QuestionTableProps> = ({...}) => {
  // Render sortable table with:
  // - Checkbox for bulk selection
  // - Links to detail page
  // - Status badges
  // - Quick actions (approve/reject buttons)
}
```

#### QuestionForm.tsx
```typescript
interface QuestionFormProps {
  question?: Question;
  onSubmit: (data: QuestionEditRequest) => Promise<void>;
  isLoading: boolean;
}

export const QuestionForm: React.FC<QuestionFormProps> = ({...}) => {
  // React Hook Form + Zod validation
  // Fields:
  // - question_text (textarea)
  // - passage_text (textarea)
  // - options A-D (4 input fields)
  // - correct answer (radio)
  // - explanation (textarea)
  // - Save / Cancel buttons
}
```

#### AnnotationPanel.tsx
```typescript
interface AnnotationPanelProps {
  annotation: QuestionAnnotation;
  options: QuestionOption[];
}

export const AnnotationPanel: React.FC<AnnotationPanelProps> = ({...}) => {
  // Display (read-only):
  // - Grammar focus keys (pills/tags)
  // - Trap keys
  // - Distractor analysis table:
  //   | Option | Role | Trap Key | Why Plausible | Why Wrong |
  // - Confidence scores (bar chart)
}
```

---

## 6. Implementation Plan

### Phase 1: Backend API Scaffolding (Week 1)

**Files to create/modify:**
1. `backend/app/routers/admin-questions.py` (new)
   - GET `/admin/questions` (list with filters)
   - GET `/admin/questions/{id}` (detail)
   - POST `/admin/questions/{id}/edit` (update)
   
2. `backend/app/routers/admin-review.py` (new)
   - GET `/admin/jobs` (queue list)
   - POST `/admin/jobs/{job_id}/questions/{q_id}/approve`
   - POST `/admin/jobs/{job_id}/questions/{q_id}/reject`

3. `backend/app/models/payload.py` (extend)
   - Add `AdminQuestionListResponse`
   - Add `AdminQuestionDetailResponse`
   - Add `AdminEditRequest`
   - Add `AdminJobResponse`

4. `backend/app/routers/main.py` (modify)
   - Register new admin routers

**Tasks:**
- [ ] Design Pydantic schemas for responses
- [ ] Implement question list with pagination & filtering
- [ ] Implement question detail endpoint (join annotation + options)
- [ ] Implement edit endpoint (create new QuestionVersion on save)
- [ ] Implement job list & approval endpoints
- [ ] Write unit tests (pytest)

### Phase 2: Frontend Scaffolding (Week 1-2)

**Files to create:**
1. `FRONTEND/src/pages/AdminDashboard.tsx` (root layout)
2. `FRONTEND/src/pages/QuestionListPage.tsx`
3. `FRONTEND/src/pages/QuestionDetailPage.tsx`
4. `FRONTEND/src/pages/ReviewQueuePage.tsx`
5. `FRONTEND/src/components/admin/*` (all components above)
6. `FRONTEND/src/api/admin/` (API client module)
7. `FRONTEND/src/types/admin.ts`

**Tasks:**
- [ ] Create admin layout (sidenav + content area)
- [ ] Scaffold QuestionTable with dummy data
- [ ] Scaffold QuestionDetail with React Hook Form
- [ ] Create React Query hooks for API calls
- [ ] Wire up API client to mock backend endpoints
- [ ] Add routing (react-router-dom) to AdminDashboard

### Phase 3: Integration & Polish (Week 2-3)

**Tasks:**
- [ ] Connect frontend to real backend API
- [ ] Add error handling (toast notifications)
- [ ] Implement loading states & skeletons
- [ ] Add permissions check (redirect non-admin users)
- [ ] Styling & responsive design (mobile/tablet)
- [ ] Unit tests for components

### Phase 4: Review Queue & Analytics (Week 3)

**Tasks:**
- [ ] Implement ReviewQueuePage (list + job detail)
- [ ] Implement approve/reject modals
- [ ] Implement AnalyticsPage (basic charts)
- [ ] Implement BulkOpsPage (reannotate trigger)

### Phase 5: QA & Deployment (Week 4)

**Tasks:**
- [ ] End-to-end testing
- [ ] Performance testing (large question lists)
- [ ] Security audit (JWT, CSRF, SQL injection)
- [ ] Documentation (user guide, API docs)
- [ ] Deploy to staging

---

## 7. API Endpoint Specifications

### 7.1 Question Management

#### GET /admin/questions
**Query Parameters:**
```
page: int = 1
limit: int = 25
status: 'draft' | 'approved' | 'rejected' | '' = ''
origin: 'official' | 'generated' | '' = ''
test: str = ''  # test name filter
focus_key: str = ''
date_from: date | null = null
date_to: date | null = null
sort_by: str = 'updated_at'  # or 'created_at', 'practice_status'
sort_dir: 'asc' | 'desc' = 'desc'
```

**Response:**
```json
{
  "questions": [
    {
      "id": "uuid",
      "source_test_name": "Test 1",
      "source_question_number": 1,
      "content_origin": "official",
      "practice_status": "approved",
      "current_question_text": "The quick...",
      "answers_correct_pct": 78.5,
      "attempt_count": 100,
      "updated_at": "2026-06-18T10:30:00Z",
      "focus_keys": ["verb_form", "subject_verb_agreement"]
    }
  ],
  "total": 450,
  "page": 1,
  "limit": 25,
  "total_pages": 18
}
```

#### GET /admin/questions/{question_id}
**Response:**
```json
{
  "id": "uuid",
  "content_origin": "official",
  "source_test_name": "Test 1",
  "source_question_number": 1,
  "practice_status": "approved",
  "current_question_text": "The quick brown...",
  "current_passage_text": "In the beginning...",
  "current_correct_option_label": "B",
  "current_explanation_text": "Option B is correct because...",
  "created_at": "2026-05-01T00:00:00Z",
  "updated_at": "2026-06-18T10:30:00Z",
  
  "annotation": {
    "id": "uuid",
    "grammar_focus_keys": ["verb_form", "subject_verb_agreement"],
    "trap_keys": ["auxiliary_verb_omission", "tense_consistency"],
    "syntactic_traps": {
      "A": "missing auxiliary verb",
      "B": "null",
      "C": "tense mismatch",
      "D": "null"
    },
    "distractor_analysis": {
      "A": {
        "distractor_type": "trap",
        "why_plausible": "Native speakers often drop auxiliaries in casual speech",
        "why_wrong": "Grammar rules require explicit auxiliary"
      },
      "B": {"distractor_type": "correct", "why_plausible": null, "why_wrong": null},
      "C": {"distractor_type": "trap", ...},
      "D": {"distractor_type": "distractor", ...}
    },
    "confidence_scores": {
      "overall": 0.92,
      "focus_key": 0.95,
      "trap_identification": 0.88
    },
    "rules_version": "v8",
    "prompt_version": "v3.0"
  },
  
  "options": [
    {
      "label": "A",
      "text": "is looking for",
      "is_correct": false,
      "option_role": "trap",
      "distractor_type_key": "auxiliary_verb_omission",
      "why_plausible": "..."
    },
    { "label": "B", "text": "are looking for", "is_correct": true, ... },
    ...
  ],
  
  "versions": [
    {
      "version_number": 1,
      "change_source": "ingestion",
      "created_at": "2026-05-01T00:00:00Z"
    }
  ],
  
  "audit_log": [
    {
      "id": "uuid",
      "admin_user_id": "admin_1",
      "action": "approved",
      "notes": "Good quality trap",
      "created_at": "2026-06-18T09:00:00Z"
    }
  ]
}
```

#### POST /admin/questions/{question_id}/edit
**Request:**
```json
{
  "question_text": "The quick brown...",
  "passage_text": "In the beginning...",
  "options": [
    {"label": "A", "text": "...", "is_correct": false},
    {"label": "B", "text": "...", "is_correct": true},
    {"label": "C", "text": "...", "is_correct": false},
    {"label": "D", "text": "...", "is_correct": false}
  ],
  "correct_answer": "B",
  "explanation_text": "...",
  "change_notes": "Clarified wording of option C"
}
```

**Response:** Updated Question object (same as GET detail)

### 7.2 Review Queue

#### GET /admin/jobs?status=needs_review&page=1&limit=25
**Response:**
```json
{
  "jobs": [
    {
      "id": "job_uuid",
      "job_type": "ingest_official",
      "content_origin": "official",
      "status": "needs_review",
      "provider_name": "deepseek",
      "model_name": "deepseek-v4-pro:cloud",
      "question_count": 27,
      "rules_version": "v8",
      "validation_errors": [
        {
          "type": "qnum_ocr_crosscheck",
          "count": 2,
          "severity": "warning"
        }
      ],
      "created_at": "2026-06-18T08:00:00Z"
    }
  ],
  "total": 5,
  "page": 1
}
```

#### GET /admin/jobs/{job_id}
**Response:**
```json
{
  "job": {
    "id": "job_uuid",
    "status": "needs_review",
    "question_count": 27,
    "validation_errors": [...],
    "created_at": "2026-06-18T08:00:00Z"
  },
  "questions": [
    {
      "id": "q_uuid",
      "source_question_number": 1,
      "current_question_text": "...",
      "issues": ["qnum_ocr_crosscheck"],
      "practice_status": "draft"
    }
  ],
  "pagination": { "total": 27, "page": 1, "limit": 20 }
}
```

#### POST /admin/jobs/{job_id}/questions/{question_id}/approve
**Request:** `{}`  
**Response:** `{"ok": true}`

#### POST /admin/jobs/{job_id}/questions/{question_id}/reject
**Request:** `{"reason": "Traps are too obvious"}`  
**Response:** `{"ok": true}`

---

## 8. Testing Strategy

### 8.1 Backend Tests
- **Unit tests:** Question CRUD, job approval logic
- **Integration tests:** Full API workflows (list → detail → edit)
- **E2E tests:** Approval flow (job load → approve → verify status)

**Framework:** pytest + pytest-asyncio

### 8.2 Frontend Tests
- **Component tests:** Table rendering, form validation
- **Integration tests:** Page workflows (load questions → filter → open detail)
- **E2E tests:** Full admin flow (login → manage question → approve job)

**Framework:** Vitest + React Testing Library

### 8.3 QA Checklist
- [ ] Pagination works correctly (go to page 2, verify data)
- [ ] Filters apply correctly (status, origin, date range)
- [ ] Sorting toggles ascending/descending
- [ ] Edit form saves changes and creates new version
- [ ] Approval updates question status to "approved"
- [ ] Rejection moves question to "rejected" with reason
- [ ] Analytics charts render without errors
- [ ] Responsive design (mobile/tablet/desktop)
- [ ] Error states display helpful messages
- [ ] Admin user without permission gets redirected

---

## 9. Security Considerations

### 9.1 Authentication
- All admin endpoints require `admin_required` decorator
- JWT token validated on each request
- CORS configured to prevent cross-origin attacks

### 9.2 Authorization
- Role-based: only users with `admin` role can access dashboard
- Question edits logged to `AdminQuestionAuditLog` with user ID
- Sensitive fields (trap keys, confidence scores) readable by admins only

### 9.3 Data Validation
- All user input validated with Pydantic schemas
- SQL injection prevented by SQLAlchemy ORM parameterization
- File uploads (if any) scanned for malware

### 9.4 Audit Trail
- Every admin action logged:
  - Question edits (old → new value)
  - Approvals/rejections (reason, admin user)
  - Bulk operations (affected count, job ID)

---

## 10. Deployment & Operations

### 10.1 Environment Setup
- Admin dashboard served from same Vite dev server as student app
- Build: `npm run build` → outputs to `/FRONTEND/dist`
- Serve: Nginx reverse proxy to FastAPI + static assets

### 10.2 Monitoring
- Sentry integration for error tracking
- Logs written to `/var/log/dsat-admin.log`
- Metrics: API response times, question edit latency, job approval throughput

### 10.3 Rollback Plan
- Database migrations reversible (Alembic)
- Admin dashboard feature-flag controlled (disable if issues arise)
- Question edits preserve version history (easy to revert)

---

## 11. Future Enhancements (Not MVP)

1. **Vocabulary Management UI**
   - Candidates → Master.json workflow
   - Promote/reject interface with dissent tracking

2. **Advanced Analytics**
   - Student learning curves (time to 80% accuracy)
   - Trap effectiveness by demographics
   - Question difficulty calibration

3. **Bulk Trap Configuration**
   - UI to edit syntactic trap parameters
   - Test/preview traps before deploying

4. **Integration with Ingestion Pipeline**
   - Real-time job monitoring
   - Streaming OCR/extraction results

5. **Question Similarity Search**
   - Find duplicates or near-duplicates
   - Cluster by focus key

6. **Automated QA Checks**
   - Grammar rule violations
   - Missing annotations
   - Distractor similarity

---

## 12. Files & Ownership

### Backend (Python)
- `backend/app/routers/admin-questions.py` — Question CRUD
- `backend/app/routers/admin-review.py` — Job approval
- `backend/app/routers/admin-analytics.py` — Metrics (future)
- `backend/app/models/payload.py` — Pydantic schemas

### Frontend (React + TypeScript)
- `FRONTEND/src/pages/AdminDashboard.tsx` — Root layout
- `FRONTEND/src/pages/QuestionListPage.tsx` — Table
- `FRONTEND/src/pages/QuestionDetailPage.tsx` — Detail + edit
- `FRONTEND/src/pages/ReviewQueuePage.tsx` — Approval queue
- `FRONTEND/src/components/admin/*` — Reusable components
- `FRONTEND/src/api/admin/` — API client module
- `FRONTEND/src/types/admin.ts` — TypeScript interfaces

### Database
- No new tables required (use existing models)
- Migrations: Optional indexes on `practice_status`, `content_origin` for query performance

---

## 13. References

**Existing Code:**
- Grammar app: `/home/jb/DSAT_REDUX_MD/grammar-app.html` (1464 lines, vanilla HTML/CSS/JS)
- Backend models: `backend/app/models/db.py`
- Admin router stub: `backend/app/routers/admin.py`
- Frontend setup: `FRONTEND/` (React + Vite)

**Key Documentation:**
- `docs/PRD/INGESTION_PRD.md` — Backend PRD
- `rules_agent_dsat_grammar_ingestion_generation_v8.md` — Grammar rules
- `CLAUDE.md` — Project-specific guidance

---

## 14. Success Metrics

**MVP (Phase 1-3):**
- ✓ Admin can list, view, edit questions
- ✓ Admin can approve/reject ingestion jobs
- ✓ All edits logged with user ID and timestamp
- ✓ <2s page load time (questions, detail view)
- ✓ 95%+ API test coverage

**Phase 4 (Analytics):**
- ✓ Admin can see % correct per focus key
- ✓ Admin can identify trap effectiveness
- ✓ Dashboard loads in <1s

**Overall:**
- ✓ Reduces manual review time by 50% (vs. raw DB queries)
- ✓ Zero data integrity issues (audit trail captures all changes)
- ✓ Admin team adoption >80% within 2 weeks
