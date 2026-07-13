# DSAT Admin Dashboard — Implementation Task Breakdown

**Status:** Ready for Implementation  
**Scope:** MVP (Phase 1-3: Question management + Review queue)  
**Effort:** ~80-120 dev hours  
**Timeline:** 3-4 weeks (1 full-time developer)

---

## Overview: What Gets Built

**MVP Deliverables:**
1. Admin Dashboard UI (React + TypeScript)
2. Question Management (list, detail, edit)
3. Review Queue (approve/reject workflow)
4. Backend API endpoints
5. Test suite (unit + integration)

**NOT in MVP:**
- Analytics dashboard (deferred to Phase 4)
- Bulk operations (deferred to Phase 4)
- Advanced filtering/search
- Vocabulary management UI

---

## Phase 1: Backend API Scaffolding (Week 1, ~30-40 hours)

### 1.1 Create Admin API Router — Questions Module

**File:** `backend/app/routers/admin_questions.py` (NEW)

```python
# admin_questions.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import admin_required
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/admin/questions", tags=["admin-questions"])

# Models (in payload.py):
# - AdminQuestionListResponse
# - AdminQuestionDetailResponse
# - AdminEditRequest
# - AdminQuestionMetadata

@router.get("", response_model=AdminQuestionListResponse)
async def list_questions(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    origin: Optional[str] = None,
    test: Optional[str] = None,
    focus_key: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = "updated_at",
    sort_dir: str = "desc",
):
    """
    List questions with pagination, filtering, sorting.
    
    Query: SELECT q FROM Question q
           WHERE (status=? OR status IS NULL)
           AND (content_origin=? OR content_origin IS NULL)
           ORDER BY {sort_by} {sort_dir}
           LIMIT {limit} OFFSET {(page-1)*limit}
    """
    # STUB: Implementation details below
    pass

@router.get("/{question_id}", response_model=AdminQuestionDetailResponse)
async def get_question_detail(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Get full question detail with annotation, options, versions, audit log.
    
    Query: SELECT q, a, opts, versions, audit FROM Question q
           LEFT JOIN QuestionAnnotation a ON q.latest_annotation_id = a.id
           LEFT JOIN QuestionOption opts ON q.id = opts.question_id
           LEFT JOIN QuestionVersion versions ON q.id = versions.question_id
           LEFT JOIN AdminQuestionAuditLog audit ON q.id = audit.question_id
           WHERE q.id = ?
    """
    pass

@router.post("/{question_id}/edit", response_model=AdminQuestionDetailResponse)
async def edit_question(
    question_id: str,
    request: AdminEditRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Update question. Creates new QuestionVersion entry and marks annotation stale.
    
    Steps:
    1. Load question by ID or 404
    2. Create QuestionVersion with change_source="admin_edit"
    3. Update Question.current_* fields
    4. Set Question.annotation_stale = True
    5. Create AdminQuestionAuditLog entry
    6. Commit
    """
    pass

@router.post("", response_model=AdminQuestionDetailResponse)
async def create_question(
    request: AdminEditRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Create new question (admin-created, not ingested).
    """
    pass

@router.delete("/{question_id}")
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Soft delete (set practice_status="rejected" with reason "admin_deleted").
    """
    pass
```

**Tasks:**
- [ ] Define Pydantic schemas in `backend/app/models/payload.py`:
  - `AdminQuestionListItemResponse` (subset of Question fields)
  - `AdminQuestionDetailResponse` (full Question + annotation + options)
  - `AdminEditRequest` (question_text, options, explanation, notes)
  - `AdminQuestionListResponse` (questions[], total, page, limit)

- [ ] Implement `list_questions()` endpoint
  - Query with filters (status, origin, test, focus_key, date range)
  - Sorting by (created_at, updated_at, practice_status)
  - Pagination (offset/limit)
  - Join annotation & options for list display (% correct from UserProgress)
  - Return paginated response

- [ ] Implement `get_question_detail()` endpoint
  - Load Question + QuestionAnnotation (latest)
  - Load all QuestionOptions
  - Load all QuestionVersions (ordered by version_number DESC)
  - Load AdminQuestionAuditLog entries (ordered by created_at DESC)
  - Return complete detail response

- [ ] Implement `edit_question()` endpoint
  - Validate request (exactly 1 correct option, non-empty text, etc.)
  - Create QuestionVersion entry (change_source="admin_edit")
  - Update Question fields (question_text, options, explanation, etc.)
  - Mark annotation_stale = True
  - Create AdminQuestionAuditLog (action="edited", notes=change_notes)
  - Commit and return updated detail

- [ ] Implement `create_question()` endpoint
  - Similar to edit, but insert new Question + QuestionVersion + QuestionOptions
  - Set content_origin="admin_created"
  - practice_status="draft"

- [ ] Implement `delete_question()` endpoint
  - Set practice_status="rejected"
  - Store rejection_reason="admin_deleted"
  - Log to AdminQuestionAuditLog

- [ ] Unit tests
  - Test list pagination (page 1 vs page 2)
  - Test filters (status, origin)
  - Test edit validation (empty question, etc.)
  - Test version creation on edit

**Estimated Effort:** 12-15 hours

---

### 1.2 Create Admin API Router — Jobs/Review Module

**File:** `backend/app/routers/admin_jobs.py` (NEW)

```python
# admin_jobs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import admin_required
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/admin/jobs", tags=["admin-jobs"])

# Models (in payload.py):
# - AdminJobResponse
# - AdminJobDetailResponse
# - AdminQuestionInJobResponse
# - ApproveQuestionRequest
# - RejectQuestionRequest
# - BulkApproveJobRequest

@router.get("", response_model=List[AdminJobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
):
    """
    List ingestion jobs, filtered by status (e.g., "needs_review").
    
    Query: SELECT j FROM QuestionJob j
           WHERE (status=? OR status IS NULL)
           ORDER BY created_at DESC
           LIMIT {limit} OFFSET {(page-1)*limit}
    """
    pass

@router.get("/{job_id}", response_model=AdminJobDetailResponse)
async def get_job_detail(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Get job detail with embedded questions (first 20).
    
    Query: SELECT j, q FROM QuestionJob j
           LEFT JOIN Question q ON q.id IN (
             SELECT question_id FROM question_job_questions
             WHERE job_id = j.id
           )
           WHERE j.id = ?
           ORDER BY q.source_question_number ASC
           LIMIT 20
    """
    pass

@router.get("/{job_id}/questions", response_model=AdminQuestionListInJobResponse)
async def get_job_questions(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Paginated list of questions in a job (used for large jobs).
    """
    pass

@router.post("/{job_id}/questions/{question_id}/approve")
async def approve_question_in_job(
    job_id: str,
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Approve individual question from job queue.
    
    Steps:
    1. Load Question by ID or 404
    2. Check that Question was produced by job_id (via question_job_questions)
    3. Set practice_status = "approved"
    4. Log to AdminQuestionAuditLog (action="approved", job_id, approved_by)
    5. Commit
    """
    pass

@router.post("/{job_id}/questions/{question_id}/reject")
async def reject_question_in_job(
    job_id: str,
    question_id: str,
    request: RejectQuestionRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Reject individual question from job queue.
    
    Steps:
    1. Load Question by ID or 404
    2. Set practice_status = "rejected"
    3. Store rejection_reason = request.reason
    4. Log to AdminQuestionAuditLog (action="rejected", reason)
    5. Commit
    """
    pass

@router.post("/{job_id}/approve")
async def approve_all_in_job(
    job_id: str,
    request: Optional[BulkApproveJobRequest] = None,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Approve all questions in a job (bulk operation).
    
    Steps:
    1. Load job by ID or 404
    2. Load all questions produced by job (via question_job_questions)
    3. For each question:
       a. If practice_status != "rejected", set to "approved"
       b. Log to AdminQuestionAuditLog
    4. Update job status to "approved"
    5. Commit
    6. Return {ok: true, approved_count: N}
    """
    pass

@router.post("/{job_id}/reject")
async def reject_all_in_job(
    job_id: str,
    request: BulkRejectJobRequest,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """
    Reject all questions in a job.
    """
    pass
```

**Tasks:**
- [ ] Define Pydantic schemas in `backend/app/models/payload.py`:
  - `AdminJobResponse` (job metadata for list)
  - `AdminJobDetailResponse` (job + first 20 questions)
  - `AdminQuestionInJobResponse` (question with issue indicators)
  - `AdminQuestionListInJobResponse` (paginated questions)
  - `ApproveQuestionRequest`, `RejectQuestionRequest`
  - `BulkApproveJobRequest`, `BulkRejectJobRequest`

- [ ] Implement `list_jobs()` endpoint
  - Filter by status (default: "needs_review")
  - Order by created_at DESC
  - Return job list with question count, error summary

- [ ] Implement `get_job_detail()` endpoint
  - Load job + first 20 questions
  - Include issue badges (if validation errors on question)
  - Return full detail

- [ ] Implement `get_job_questions()` (paginated)
  - Return paginated questions in job

- [ ] Implement `approve_question_in_job()` endpoint
  - Validate question belongs to job
  - Set practice_status = "approved"
  - Log to AdminQuestionAuditLog

- [ ] Implement `reject_question_in_job()` endpoint
  - Similar to approve, but set to "rejected" with reason

- [ ] Implement `approve_all_in_job()` endpoint
  - Bulk approve all non-rejected questions
  - Update job status
  - Return count

- [ ] Implement `reject_all_in_job()` endpoint
  - Bulk reject all questions with reason
  - Update job status

- [ ] Unit tests
  - Test approve single question
  - Test reject with reason
  - Test bulk approve
  - Test error handling (job not found)

**Estimated Effort:** 10-12 hours

---

### 1.3 Update Database Models

**File:** `backend/app/models/db.py` (MODIFY)

**Tasks:**
- [ ] Verify `AdminQuestionAuditLog` exists
  - Should have: id, question_id, admin_user_id, action, notes, created_at
  - If missing, add model definition (see below)

- [ ] Verify indices exist for performance:
  - `question_annotations.question_id`
  - `question_options.question_id`
  - `question_jobs.status`
  - `questions.practice_status`
  - `questions.content_origin`

- [ ] Add `AdminQuestionAuditLog` model (if missing)
  ```python
  class AdminQuestionAuditLog(Base):
      __tablename__ = "admin_question_audit_logs"
      
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
      admin_user_id = Column(String(128), nullable=False)
      action = Column(String(50), nullable=False)  # "edited", "approved", "rejected"
      notes = Column(Text, nullable=True)
      created_at = Column(DateTime(timezone=True), default=_utcnow)
      
      question = relationship("Question", foreign_keys=[question_id])
  ```

**Estimated Effort:** 2-3 hours

---

### 1.4 Update Payload Models

**File:** `backend/app/models/payload.py` (MODIFY)

**Tasks:**
- [ ] Add schemas:
  ```python
  class AdminQuestionListItemResponse(BaseModel):
      id: str
      source_test_name: str
      source_question_number: int
      content_origin: str
      practice_status: str
      current_question_text: str
      answers_correct_pct: Optional[float]
      attempt_count: int
      updated_at: datetime
      focus_keys: List[str]
  
  class AdminQuestionListResponse(BaseModel):
      questions: List[AdminQuestionListItemResponse]
      total: int
      page: int
      limit: int
      total_pages: int
  
  class AdminEditRequest(BaseModel):
      question_text: str
      passage_text: Optional[str] = None
      options: List[AdminOptionInput]  # {label, text, is_correct}
      correct_answer: str  # "A", "B", "C", "D"
      explanation_text: str
      change_notes: Optional[str] = None
      
      @validator('options')
      def validate_options(cls, v):
          if len(v) != 4:
              raise ValueError("Must have exactly 4 options")
          # One must be correct
          correct_count = sum(1 for o in v if o.is_correct)
          if correct_count != 1:
              raise ValueError("Must have exactly one correct option")
          return v
  
  # Similar for AdminJobResponse, etc.
  ```

**Estimated Effort:** 4-6 hours

---

### 1.5 Register Routes in Main App

**File:** `backend/app/routers/__init__.py` (MODIFY) or `backend/app/main.py`

**Tasks:**
- [ ] Import new routers
  ```python
  from app.routers import admin_questions, admin_jobs
  ```
- [ ] Register with FastAPI app
  ```python
  app.include_router(admin_questions.router)
  app.include_router(admin_jobs.router)
  ```

**Estimated Effort:** 1 hour

---

### 1.6 Backend Tests

**File:** `backend/tests/test_admin_questions.py` (NEW)

**Tasks:**
- [ ] Setup fixtures (sample questions, jobs, annotations)
  ```python
  @pytest.fixture
  async def sample_question(db_session):
      q = Question(
          content_origin="official",
          practice_status="draft",
          current_question_text="Sample question",
          current_correct_option_label="B",
      )
      db_session.add(q)
      await db_session.flush()
      return q
  ```

- [ ] Test `list_questions()`
  - Test pagination (page 1 vs page 2)
  - Test filters (status="approved", origin="official")
  - Test sorting (updated_at ASC vs DESC)
  - Test empty list

- [ ] Test `get_question_detail()`
  - Test retrieval of full detail
  - Test 404 on missing question
  - Test annotation included

- [ ] Test `edit_question()`
  - Test successful edit
  - Test validation errors (no correct option)
  - Test version creation
  - Test audit log entry

- [ ] Test job endpoints
  - Test list jobs by status
  - Test approve single question
  - Test reject with reason
  - Test bulk approve

- [ ] Test error handling
  - 404 on missing resources
  - 403 on non-admin user
  - 422 on invalid input

**Estimated Effort:** 8-10 hours

---

## Phase 2: Frontend Scaffolding (Week 1-2, ~30-40 hours)

### 2.1 Create React Component Structure

**Directory Setup:**

```bash
mkdir -p FRONTEND/src/pages/admin
mkdir -p FRONTEND/src/components/admin
mkdir -p FRONTEND/src/api/admin
mkdir -p FRONTEND/src/hooks
mkdir -p FRONTEND/src/types
```

### 2.2 Create TypeScript Types

**File:** `FRONTEND/src/types/admin.ts` (NEW)

```typescript
// admin.ts
export interface Question {
  id: string;
  source_test_name: string;
  source_question_number: number;
  content_origin: "official" | "generated" | "admin_created";
  practice_status: "draft" | "approved" | "rejected";
  current_question_text: string;
  current_passage_text?: string;
  current_correct_option_label: string;
  current_explanation_text: string;
  answers_correct_pct?: number;
  attempt_count: number;
  updated_at: string;
  created_at: string;
  focus_keys?: string[];
}

export interface QuestionOption {
  id: string;
  label: "A" | "B" | "C" | "D";
  text: string;
  is_correct: boolean;
  option_role: string;
  distractor_type_key?: string;
  why_plausible?: string;
  why_wrong?: string;
}

export interface QuestionAnnotation {
  id: string;
  grammar_focus_keys?: string[];
  trap_keys?: string[];
  syntactic_traps?: Record<string, string>;
  distractor_analysis?: Record<string, DistractorInfo>;
  confidence_scores?: Record<string, number>;
  rules_version: string;
  prompt_version: string;
}

export interface DistractorInfo {
  distractor_type: string;
  why_plausible?: string;
  why_wrong?: string;
}

export interface QuestionDetail extends Question {
  annotation?: QuestionAnnotation;
  options: QuestionOption[];
  versions: QuestionVersion[];
  audit_log: AuditLogEntry[];
}

export interface QuestionVersion {
  version_number: number;
  change_source: string;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  admin_user_id: string;
  action: "edited" | "approved" | "rejected";
  notes?: string;
  created_at: string;
}

export interface AdminEditRequest {
  question_text: string;
  passage_text?: string;
  options: Array<{ label: string; text: string; is_correct: boolean }>;
  correct_answer: "A" | "B" | "C" | "D";
  explanation_text: string;
  change_notes?: string;
}

export interface QuestionListResponse {
  questions: Question[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

// Job types
export interface QuestionJob {
  id: string;
  job_type: string;
  content_origin: string;
  status: "pending" | "in_progress" | "needs_review" | "approved" | "rejected" | "failed";
  question_count: number;
  validation_errors?: Array<{ type: string; count: number; severity: string }>;
  created_at: string;
}

export interface JobDetail extends QuestionJob {
  questions: Array<Question & { issues?: string[] }>;
}
```

**Tasks:**
- [ ] Define all TypeScript interfaces matching API responses
- [ ] Export from central types/admin.ts file

**Estimated Effort:** 2-3 hours

---

### 2.3 Create API Client

**File:** `FRONTEND/src/api/admin/questions.ts` (NEW)

```typescript
// questions.ts
import { API_BASE_URL } from "../config";
import { Question, QuestionDetail, QuestionListResponse, AdminEditRequest } from "../../types/admin";

export const fetchQuestions = async (
  page: number = 1,
  limit: number = 25,
  filters?: {
    status?: string;
    origin?: string;
    test?: string;
    focus_key?: string;
  }
): Promise<QuestionListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...filters,
  });
  const response = await fetch(`${API_BASE_URL}/admin/questions?${params}`);
  if (!response.ok) throw new Error("Failed to fetch questions");
  return response.json();
};

export const fetchQuestionDetail = async (questionId: string): Promise<QuestionDetail> => {
  const response = await fetch(`${API_BASE_URL}/admin/questions/${questionId}`);
  if (!response.ok) throw new Error("Failed to fetch question");
  return response.json();
};

export const editQuestion = async (
  questionId: string,
  data: AdminEditRequest
): Promise<QuestionDetail> => {
  const response = await fetch(`${API_BASE_URL}/admin/questions/${questionId}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to edit question");
  return response.json();
};

export const createQuestion = async (data: AdminEditRequest): Promise<QuestionDetail> => {
  const response = await fetch(`${API_BASE_URL}/admin/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create question");
  return response.json();
};

export const deleteQuestion = async (questionId: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/admin/questions/${questionId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete question");
};
```

**File:** `FRONTEND/src/api/admin/jobs.ts` (NEW)

```typescript
// Similar pattern for job endpoints
export const fetchJobs = async (status?: string) => { ... }
export const fetchJobDetail = async (jobId: string) => { ... }
export const approveQuestion = async (jobId: string, questionId: string) => { ... }
export const rejectQuestion = async (jobId: string, questionId: string, reason: string) => { ... }
export const approveAllInJob = async (jobId: string) => { ... }
```

**Tasks:**
- [ ] Create API client functions for all admin endpoints
- [ ] Add error handling and logging
- [ ] Use consistent response/request formatting

**Estimated Effort:** 4-6 hours

---

### 2.4 Create React Query Hooks

**File:** `FRONTEND/src/hooks/useQuestions.ts` (NEW)

```typescript
// useQuestions.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as questionsApi from "../api/admin/questions";
import { Question, QuestionDetail, AdminEditRequest } from "../types/admin";

export const useQuestions = (
  page: number = 1,
  limit: number = 25,
  filters?: Record<string, string>
) => {
  return useQuery({
    queryKey: ["questions", page, limit, filters],
    queryFn: () => questionsApi.fetchQuestions(page, limit, filters),
    staleTime: 30000, // 30 seconds
  });
};

export const useQuestionDetail = (questionId: string) => {
  return useQuery({
    queryKey: ["question", questionId],
    queryFn: () => questionsApi.fetchQuestionDetail(questionId),
    staleTime: 30000,
  });
};

export const useEditQuestion = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AdminEditRequest }) =>
      questionsApi.editQuestion(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(["question", data.id], data);
      queryClient.invalidateQueries({ queryKey: ["questions"] });
    },
  });
};

// Similar hooks for jobs, etc.
```

**Tasks:**
- [ ] Create useQuestions hook (list with caching)
- [ ] Create useQuestionDetail hook
- [ ] Create useEditQuestion mutation
- [ ] Create useJobs, useJobDetail hooks
- [ ] Create useApproveQuestion mutation
- [ ] Create useRejectQuestion mutation

**Estimated Effort:** 6-8 hours

---

### 2.5 Create Admin Layout & Navigation

**File:** `FRONTEND/src/pages/AdminDashboard.tsx` (NEW)

```typescript
import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidenav from "../components/admin/Sidenav";
import Header from "../components/admin/Header";
import QuestionListPage from "./admin/QuestionListPage";
import QuestionDetailPage from "./admin/QuestionDetailPage";
import ReviewQueuePage from "./admin/ReviewQueuePage";

export const AdminDashboard: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidenav */}
      <Sidenav open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main content */}
      <div className="flex flex-col flex-1">
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        
        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/questions" element={<QuestionListPage />} />
            <Route path="/questions/:id" element={<QuestionDetailPage />} />
            <Route path="/review-queue" element={<ReviewQueuePage />} />
            <Route path="/" element={<Navigate to="/questions" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
```

**File:** `FRONTEND/src/components/admin/Sidenav.tsx` (NEW)

```typescript
// Sidenav component with navigation tabs
interface SidenavProps {
  open: boolean;
  onToggle: () => void;
}

export const Sidenav: React.FC<SidenavProps> = ({ open, onToggle }) => {
  return (
    <aside className={`
      fixed inset-y-0 left-0 z-40 w-64 bg-gray-900 text-white
      transform transition-transform duration-200
      ${open ? "translate-x-0" : "-translate-x-full"}
      lg:relative lg:translate-x-0
    `}>
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-xl font-bold">DSAT Admin</h1>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-2">
        <NavLink to="/admin/questions" icon="📋">Questions</NavLink>
        <NavLink to="/admin/review-queue" icon="✓">Review Queue</NavLink>
        <NavLink to="/admin/analytics" icon="📊">Analytics</NavLink>
        <NavLink to="/admin/bulk-ops" icon="⚙️">Bulk Ops</NavLink>
      </nav>

      {/* User info */}
      <div className="absolute bottom-0 w-full p-4 border-t border-gray-800">
        <button className="text-sm text-gray-400 hover:text-white">Logout</button>
      </div>
    </aside>
  );
};
```

**File:** `FRONTEND/src/components/admin/Header.tsx` (NEW)

```typescript
// Header component with title and notifications
interface HeaderProps {
  onMenuClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6 gap-4">
      <button onClick={onMenuClick} className="lg:hidden">
        ☰
      </button>
      <h2 className="text-xl font-semibold text-gray-900">Questions</h2>
      <div className="ml-auto flex items-center gap-4">
        <button className="relative">
          🔔
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
      </div>
    </header>
  );
};
```

**Tasks:**
- [ ] Create AdminDashboard layout wrapper
- [ ] Create Sidenav with navigation tabs
- [ ] Create Header with title/notifications
- [ ] Setup React Router for admin routes
- [ ] Add responsive design (mobile menu collapse)

**Estimated Effort:** 6-8 hours

---

### 2.6 Create Question List Page

**File:** `FRONTEND/src/pages/admin/QuestionListPage.tsx` (NEW)

```typescript
import React, { useState } from "react";
import { useQuestions } from "../../hooks/useQuestions";
import QuestionTable from "../../components/admin/QuestionTable";
import FilterBar from "../../components/admin/FilterBar";

export const QuestionListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({});

  const { data, isLoading, error } = useQuestions(page, 25, filters);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Questions</h1>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          + Create Question
        </button>
      </div>

      {/* Filters */}
      <FilterBar onFiltersChange={setFilters} />

      {/* Table */}
      {isLoading ? (
        <div>Loading...</div>
      ) : error ? (
        <div className="text-red-600">Error loading questions</div>
      ) : (
        <>
          <QuestionTable data={data?.questions || []} />
          
          {/* Pagination */}
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Showing {(page - 1) * 25 + 1}-{Math.min(page * 25, data?.total || 0)} of {data?.total}
            </div>
            <div className="space-x-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                ← Prev
              </button>
              <span className="text-sm text-gray-600">Page {page} of {data?.total_pages}</span>
              <button
                disabled={page === data?.total_pages}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50"
              >
                Next →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default QuestionListPage;
```

**File:** `FRONTEND/src/components/admin/QuestionTable.tsx` (NEW)

```typescript
interface QuestionTableProps {
  data: Question[];
}

export const QuestionTable: React.FC<QuestionTableProps> = ({ data }) => {
  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="p-3 text-left font-medium text-gray-700">ID</th>
            <th className="p-3 text-left font-medium text-gray-700">Test</th>
            <th className="p-3 text-left font-medium text-gray-700">Q#</th>
            <th className="p-3 text-left font-medium text-gray-700">Status</th>
            <th className="p-3 text-left font-medium text-gray-700">% Correct</th>
            <th className="p-3 text-left font-medium text-gray-700">Updated</th>
            <th className="p-3 text-left font-medium text-gray-700">Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map((q) => (
            <tr key={q.id} className="border-b border-gray-200 hover:bg-gray-50">
              <td className="p-3">
                <Link to={`/admin/questions/${q.id}`} className="text-blue-600 hover:underline">
                  {q.id.slice(0, 8)}
                </Link>
              </td>
              <td className="p-3">{q.source_test_name}</td>
              <td className="p-3">{q.source_question_number}</td>
              <td className="p-3">
                <StatusBadge status={q.practice_status} />
              </td>
              <td className="p-3">{q.answers_correct_pct?.toFixed(0)}%</td>
              <td className="p-3">{formatDate(q.updated_at)}</td>
              <td className="p-3">
                <MoreActionsMenu questionId={q.id} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

**File:** `FRONTEND/src/components/admin/FilterBar.tsx` (NEW)

```typescript
// Collapsible filter bar with status, origin, test, focus_key
export const FilterBar: React.FC<{ onFiltersChange: (f: any) => void }> = ({
  onFiltersChange,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [filters, setFilters] = useState({});

  const handleChange = (key: string, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-900">Filters</h3>
        <button onClick={() => setExpanded(!expanded)}>
          {expanded ? "▼" : "▶"}
        </button>
      </div>

      {expanded && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <select
            value={filters.status || ""}
            onChange={(e) => handleChange("status", e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          {/* Similar for origin, test, focus_key */}
          <button
            onClick={() => {
              setFilters({});
              onFiltersChange({});
            }}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
          >
            Reset
          </button>
        </div>
      )}
    </div>
  );
};
```

**Tasks:**
- [ ] Create QuestionListPage component
- [ ] Create QuestionTable with sortable columns
- [ ] Create FilterBar with collapsible filters
- [ ] Create StatusBadge component (reusable)
- [ ] Add pagination controls
- [ ] Add "Create Question" button (links to form modal)
- [ ] Wire up useQuestions hook
- [ ] Add loading skeleton/spinner
- [ ] Add error handling with toast

**Estimated Effort:** 10-12 hours

---

### 2.7 Create Question Detail & Edit Pages

**File:** `FRONTEND/src/pages/admin/QuestionDetailPage.tsx` (NEW)

```typescript
// Detail page with collapsible sections
export const QuestionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: question, isLoading } = useQuestionDetail(id);
  const [editMode, setEditMode] = useState(false);

  if (isLoading) return <div>Loading...</div>;
  if (!question) return <div>Question not found</div>;

  return (
    <div className="space-y-6">
      {/* Back button & header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Link to="/admin/questions" className="text-blue-600">← Back</Link>
          <h1 className="text-2xl font-bold">Q#{question.source_question_number}</h1>
        </div>
        <div className="space-x-2">
          <button onClick={() => setEditMode(!editMode)} className="px-4 py-2 border rounded">
            Edit
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded">Approve</button>
          <button className="px-4 py-2 bg-red-600 text-white rounded">Reject</button>
        </div>
      </div>

      {/* Status badge */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <StatusBadge status={question.practice_status} />
      </div>

      {/* Question content */}
      <QuestionDisplay question={question} />

      {/* Annotation panel */}
      <AnnotationPanel annotation={question.annotation} options={question.options} />

      {/* Version history */}
      <VersionHistory versions={question.versions} />

      {/* Audit log */}
      <AuditLog entries={question.audit_log} />

      {/* Edit form (modal) */}
      {editMode && (
        <QuestionForm
          question={question}
          onSubmit={handleSubmit}
          onCancel={() => setEditMode(false)}
        />
      )}
    </div>
  );
};
```

**File:** `FRONTEND/src/components/admin/QuestionForm.tsx` (NEW)

```typescript
export const QuestionForm: React.FC<QuestionFormProps> = ({
  question,
  onSubmit,
  onCancel,
}) => {
  const form = useForm<AdminEditRequest>({
    defaultValues: question
      ? {
          question_text: question.current_question_text,
          passage_text: question.current_passage_text,
          options: question.options.map((o) => ({
            label: o.label,
            text: o.text,
            is_correct: o.is_correct,
          })),
          correct_answer: question.current_correct_option_label,
          explanation_text: question.current_explanation_text,
        }
      : {},
  });

  const handleFormSubmit = async (data: AdminEditRequest) => {
    try {
      await onSubmit(data);
      // Success toast
    } catch (error) {
      // Error toast
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-screen overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6">Edit Question</h2>

        <form onSubmit={form.handleSubmit(handleFormSubmit)} className="space-y-6">
          {/* Question text */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Question Text *
            </label>
            <textarea
              {...form.register("question_text", { required: "Required" })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            {form.formState.errors.question_text && (
              <p className="text-red-600 text-sm mt-1">
                {form.formState.errors.question_text.message}
              </p>
            )}
          </div>

          {/* Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Options *</label>
            <div className="space-y-3">
              {form.watch("options")?.map((_, idx) => (
                <div key={idx} className="grid grid-cols-4 gap-2 items-center">
                  <input
                    {...form.register(`options.${idx}.label`)}
                    disabled
                    className="px-2 py-1 bg-gray-100 rounded text-center"
                  />
                  <textarea
                    {...form.register(`options.${idx}.text`, { required: "Required" })}
                    rows={2}
                    className="col-span-2 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <label className="flex items-center">
                    <input
                      type="radio"
                      {...form.register("correct_answer")}
                      value={String.fromCharCode(65 + idx)} // A, B, C, D
                    />
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Explanation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Explanation *
            </label>
            <textarea
              {...form.register("explanation_text", { required: "Required" })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          {/* Change notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Change Notes
            </label>
            <textarea
              {...form.register("change_notes")}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              placeholder="Optional notes about this edit"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

**File:** `FRONTEND/src/components/admin/AnnotationPanel.tsx` (NEW)

```typescript
// Read-only display of annotation, confidence scores, distractor analysis
export const AnnotationPanel: React.FC<AnnotationPanelProps> = ({
  annotation,
  options,
}) => {
  if (!annotation) return <div>No annotation available</div>;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Annotation</h3>

      {/* Focus keys */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Grammar Focus Keys</p>
        <div className="flex flex-wrap gap-2">
          {annotation.grammar_focus_keys?.map((key) => (
            <span key={key} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              {key}
            </span>
          ))}
        </div>
      </div>

      {/* Trap keys */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Trap Keys</p>
        <div className="flex flex-wrap gap-2">
          {annotation.trap_keys?.map((key) => (
            <span key={key} className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
              {key}
            </span>
          ))}
        </div>
      </div>

      {/* Confidence scores */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Confidence Scores</p>
        {Object.entries(annotation.confidence_scores || {}).map(([key, value]) => (
          <div key={key} className="mb-2">
            <div className="flex justify-between text-sm mb-1">
              <span className="capitalize">{key}</span>
              <span>{(value * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded h-2">
              <div
                className="bg-green-500 h-2 rounded"
                style={{ width: `${value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Distractor analysis table */}
      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">Distractor Analysis</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-50">
                <th className="border border-gray-200 p-2 text-left font-medium">Option</th>
                <th className="border border-gray-200 p-2 text-left font-medium">Role</th>
                <th className="border border-gray-200 p-2 text-left font-medium">
                  Why Plausible
                </th>
                <th className="border border-gray-200 p-2 text-left font-medium">Why Wrong</th>
              </tr>
            </thead>
            <tbody>
              {options.map((opt) => (
                <tr key={opt.label}>
                  <td className="border border-gray-200 p-2 font-semibold">{opt.label}</td>
                  <td className="border border-gray-200 p-2">
                    {opt.is_correct ? "✓ Correct" : opt.distractor_type_key || "—"}
                  </td>
                  <td className="border border-gray-200 p-2 text-xs">
                    {opt.why_plausible || "—"}
                  </td>
                  <td className="border border-gray-200 p-2 text-xs">
                    {opt.why_wrong || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
```

**Tasks:**
- [ ] Create QuestionDetailPage
- [ ] Create QuestionForm with React Hook Form + Zod validation
- [ ] Create AnnotationPanel (read-only display)
- [ ] Create VersionHistory component
- [ ] Create AuditLog component
- [ ] Create StatusBadge & other reusable components
- [ ] Wire up edit mutation
- [ ] Add approve/reject buttons (opens modal)

**Estimated Effort:** 14-18 hours

---

### 2.8 Create Review Queue Page

**File:** `FRONTEND/src/pages/admin/ReviewQueuePage.tsx` (NEW)

```typescript
// Similar structure: list jobs → expand job → inline approve/reject per question
export const ReviewQueuePage: React.FC = () => {
  const { data: jobs, isLoading } = useJobs({ status: "needs_review" });
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Review Queue</h1>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div className="space-y-4">
          {jobs?.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              expanded={expandedJobId === job.id}
              onToggle={() =>
                setExpandedJobId(expandedJobId === job.id ? null : job.id)
              }
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const JobCard: React.FC<JobCardProps> = ({ job, expanded, onToggle }) => {
  const { data: jobDetail } = useJobDetail(job.id, expanded);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-start cursor-pointer" onClick={onToggle}>
        <div>
          <h3 className="font-semibold text-gray-900">
            {job.job_type}: {job.question_count} questions
          </h3>
          <p className="text-sm text-gray-600">ID: {job.id.slice(0, 8)}</p>
          <StatusBadge status={job.status} />
        </div>
        <span>{expanded ? "▼" : "▶"}</span>
      </div>

      {/* Expanded content */}
      {expanded && jobDetail && (
        <div className="mt-4 space-y-3 border-t pt-4">
          {jobDetail.questions.map((q) => (
            <QuestionInJobRow key={q.id} question={q} jobId={job.id} />
          ))}
          
          {/* Bulk actions */}
          <div className="flex gap-2 mt-4">
            <button className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
              Approve All
            </button>
            <button className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
              Reject All
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export const QuestionInJobRow: React.FC<{ question: Question; jobId: string }> = ({
  question,
  jobId,
}) => {
  const [rejectOpen, setRejectOpen] = useState(false);
  const approveQMutation = useApproveQuestion();
  const rejectQMutation = useRejectQuestion();

  return (
    <div className="p-3 bg-gray-50 rounded border border-gray-200">
      <div className="flex justify-between items-start">
        <div>
          <p className="font-medium text-gray-900">Q#{question.source_question_number}</p>
          <p className="text-sm text-gray-600 line-clamp-2">
            {question.current_question_text}
          </p>
          {question.issues && (
            <div className="flex gap-1 mt-1">
              {question.issues.map((issue) => (
                <span
                  key={issue}
                  className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded text-xs"
                >
                  ⚠ {issue}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={() =>
              approveQMutation.mutate({ jobId, questionId: question.id })
            }
            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
            disabled={approveQMutation.isPending}
          >
            ✓ Approve
          </button>
          <button
            onClick={() => setRejectOpen(true)}
            className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
          >
            ✕ Reject
          </button>
          <Link
            to={`/admin/questions/${question.id}`}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"
          >
            View
          </Link>
        </div>
      </div>

      {/* Reject modal */}
      {rejectOpen && (
        <RejectModal
          question={question}
          onReject={(reason) => {
            rejectQMutation.mutate({ jobId, questionId: question.id, reason });
            setRejectOpen(false);
          }}
          onCancel={() => setRejectOpen(false)}
        />
      )}
    </div>
  );
};
```

**Tasks:**
- [ ] Create ReviewQueuePage
- [ ] Create JobCard (collapsible)
- [ ] Create QuestionInJobRow (inline preview)
- [ ] Create RejectModal
- [ ] Wire up approve/reject mutations
- [ ] Add bulk approve/reject for entire job
- [ ] Add error handling

**Estimated Effort:** 10-12 hours

---

## Phase 3: Integration & Polish (Week 2-3, ~20-30 hours)

### 3.1 Error Handling & Notifications

**File:** `FRONTEND/src/components/admin/Toast.tsx` (NEW)

```typescript
// Toast notification system (reusable)
export const useToast = () => {
  // Use context or state to manage toasts
  const showSuccess = (message: string) => { ... }
  const showError = (message: string) => { ... }
};
```

**Tasks:**
- [ ] Add error boundary component
- [ ] Implement toast notification system
- [ ] Add error messages to all API calls
- [ ] Add validation error display in forms
- [ ] Handle network timeout errors gracefully

**Estimated Effort:** 4-5 hours

---

### 3.2 Loading States & Skeletons

**Tasks:**
- [ ] Add skeleton loaders for table rows
- [ ] Add loading spinners on buttons
- [ ] Add skeleton for detail page
- [ ] Disable interactions while loading

**Estimated Effort:** 3-4 hours

---

### 3.3 Permission Checks

**File:** `FRONTEND/src/components/PrivateRoute.tsx` (NEW)

```typescript
// Check if user is admin before rendering admin pages
export const AdminRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const isAdmin = useIsAdmin(); // Check from JWT or context

  if (!isAdmin) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
```

**Tasks:**
- [ ] Check JWT token for admin role
- [ ] Redirect non-admins to login
- [ ] Show permission denied message if needed

**Estimated Effort:** 2-3 hours

---

### 3.4 Responsive Design

**Tasks:**
- [ ] Test on mobile (375px), tablet (768px), desktop (1440px)
- [ ] Adjust table to stack on mobile
- [ ] Adjust sidenav to collapse on mobile
- [ ] Test form inputs on mobile keyboards
- [ ] Adjust modal sizing

**Estimated Effort:** 4-6 hours

---

### 3.5 Styling & Polish

**Tasks:**
- [ ] Add Tailwind CSS classes throughout
- [ ] Ensure consistent spacing (p-2, p-4, p-6)
- [ ] Use consistent color palette (blue-600 for primary, red-600 for danger)
- [ ] Add hover states on all interactive elements
- [ ] Add transitions/animations for smooth UX
- [ ] Test in light/dark mode (if supported)

**Estimated Effort:** 6-8 hours

---

### 3.6 Unit Tests (Frontend)

**File:** `FRONTEND/src/__tests__/components/admin/QuestionTable.test.tsx` (NEW)

```typescript
import { render, screen } from "@testing-library/react";
import QuestionTable from "../../../../components/admin/QuestionTable";

describe("QuestionTable", () => {
  it("renders questions", () => {
    const questions = [
      {
        id: "1",
        source_test_name: "Test 1",
        source_question_number: 1,
        // ...
      },
    ];
    render(<QuestionTable data={questions} />);
    expect(screen.getByText("Test 1")).toBeInTheDocument();
  });
});
```

**Tasks:**
- [ ] Test QuestionTable rendering
- [ ] Test QuestionForm validation
- [ ] Test FilterBar
- [ ] Test hooks (useQuestions, etc.)
- [ ] Test error states

**Estimated Effort:** 6-8 hours

---

## Phase 4: Analytics & Bulk Ops (Week 3-4, ~20-30 hours)

### 4.1 Analytics Page

**File:** `FRONTEND/src/pages/admin/AnalyticsPage.tsx` (NEW)

```typescript
// Create KPI cards, performance table, trap effectiveness table
// Use Chart.js or Recharts for visualizations
```

**Backend endpoints (new):**
- `GET /admin/analytics/performance` — By focus key
- `GET /admin/analytics/traps` — Top traps
- `GET /admin/analytics/coverage` — Questions per focus key

**Tasks:**
- [ ] Create analytics backend endpoints
- [ ] Create KPI card components
- [ ] Create performance chart (bar or line)
- [ ] Create trap effectiveness table
- [ ] Add date range selector
- [ ] Wire up analytics data

**Estimated Effort:** 12-15 hours

---

### 4.2 Bulk Operations Page

**File:** `FRONTEND/src/pages/admin/BulkOpsPage.tsx` (NEW)

```typescript
// Re-annotate, bulk update focus keys
// Show job history with progress bars
```

**Backend endpoints (new):**
- `POST /admin/bulk/reannotate` — Queue reannotation job
- `POST /admin/bulk/update-focus-key` — Bulk update
- `GET /admin/bulk/job/{id}` — Check job progress

**Tasks:**
- [ ] Create bulk operation interfaces
- [ ] Create reannotate form (question selection)
- [ ] Create focus key update form
- [ ] Create job progress tracker
- [ ] Add WebSocket or polling for live progress

**Estimated Effort:** 10-12 hours

---

## Summary: Total Effort

| Phase | Component | Hours | Status |
|-------|-----------|-------|--------|
| 1 | Backend API Scaffolding | 40 | Ready |
| 2 | Frontend Components | 60 | Ready |
| 3 | Integration & Polish | 25 | Ready |
| 4 | Analytics & Bulk Ops | 30 | Future |
| **MVP Total** | | **125** | |

**Timeline: 3-4 weeks at 40 hours/week**

---

## Implementation Order (Recommended)

1. **Week 1:** Backend API scaffolding (Phase 1) + Basic frontend setup (Phase 2.1-2.2)
2. **Week 2:** Complete frontend components (Phase 2.3-2.8) + Basic integration (Phase 3.1-3.3)
3. **Week 3:** Polish & testing (Phase 3.4-3.6) + Review queue refinement
4. **Week 4:** Analytics & bulk ops (Phase 4) + QA & deployment

---

## Risk & Mitigation

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| API response times slow on large datasets | Medium | Add pagination, caching, indexes |
| Frontend form validation too strict | Medium | Test with real data, iterate |
| Admin permission check missed | Low | Add unit tests for auth |
| Mobile responsiveness broken | Low | Test on real devices early |
| Database migrations fail | Low | Test locally before prod |

---

## Success Criteria

- ✓ Admin can list questions with filters/pagination
- ✓ Admin can view question detail with full annotation
- ✓ Admin can edit question and create version
- ✓ Admin can approve/reject questions from job queue
- ✓ All changes logged to audit trail
- ✓ <2s page load time for question lists
- ✓ 95%+ test coverage
- ✓ Admin team adoption within 2 weeks
