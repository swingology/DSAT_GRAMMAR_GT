# DSAT Admin Dashboard — Complete Design Package

**Overview:** A comprehensive design and implementation plan for a web-based admin dashboard to manage DSAT grammar practice questions, review ingestion pipelines, and analyze question performance.

**Status:** Design Complete (Ready for Implementation)  
**Date:** 2026-06-18  
**Scope:** MVP (Phases 1-3) + Future (Phases 4+)

---

## Quick Start for Developers

### What You're Getting

This package contains 4 comprehensive design documents:

1. **ADMIN_DASHBOARD_DESIGN.md** (Main Design Doc)
   - System architecture & data flow
   - Complete feature breakdown with wireframes
   - API endpoint specifications (detailed)
   - Database & model design
   - Testing strategy & security considerations
   - **Read this first** to understand the "what" and "why"

2. **ADMIN_DASHBOARD_WIREFRAMES.md** (Visual Guide)
   - ASCII wireframes for all major pages
   - Component hierarchy diagram
   - Responsive design breakpoints
   - Color palette & typography
   - Accessibility requirements
   - **Reference this when building components**

3. **ADMIN_DASHBOARD_TASKS.md** (Implementation Roadmap)
   - Phase-by-phase breakdown
   - Concrete file paths & code stubs
   - Task checklists with effort estimates
   - Risk assessment & mitigation
   - **Use this to plan sprints**

4. **This File** (README)
   - Quick reference & navigation
   - Key decisions & assumptions
   - Deliverables checklist
   - How to start implementation

---

## Key Design Decisions

### 1. Tech Stack (Fixed)
- **Frontend:** React 18 + TypeScript + Vite (extends existing `/FRONTEND`)
- **Backend:** FastAPI (extend existing `/backend/app/routers/admin.py`)
- **Database:** PostgreSQL (use existing models in `/backend/app/models/db.py`)
- **Styling:** Tailwind CSS (matches `grammar-app.html` palette)

**Rationale:** Reuses existing infrastructure, minimizes new dependencies, familiar to team.

### 2. Phased Delivery (MVP First)
- **MVP (Phases 1-3):** Question management + Review queue
- **Future (Phase 4):** Analytics & bulk operations

**Rationale:** MVP delivers value in 3 weeks, analytics can iterate separately.

### 3. API Design (RESTful + Pagination)
- List endpoints use offset/limit pagination (not cursor)
- All mutations return full updated resource (not just status)
- Errors use standard HTTP status codes + JSON body

**Rationale:** Simpler to implement, easier to debug, works well with React Query.

### 4. Authentication (Reuse Existing)
- Use existing `app.auth.admin_required` decorator on all admin routes
- JWT-based, cookie or Authorization header
- No new auth system needed

**Rationale:** Integrates with existing student auth, reduces attack surface.

### 5. Audit Trail (Mandatory)
- Every admin action logged to `AdminQuestionAuditLog` table
- Includes user ID, timestamp, action type, notes
- Immutable (never delete audit logs)

**Rationale:** Compliance requirement for educational data, enables debugging.

---

## Core Workflows

### Workflow 1: Question Management
```
Admin → List Questions [page 1 of 18]
     → Click Question #1
     → View Question Detail (full annotation)
     → [Edit] → QuestionForm modal
     → Save → Creates new QuestionVersion
     → Confirms save + shows audit entry
```

### Workflow 2: Job Approval
```
Job arrives from ingestion pipeline (status: needs_review)
Admin → Review Queue page
     → Job shows 27 questions
     → For each question: [Approve] or [Reject with reason]
     → Bulk option: [Approve All] or [Reject All]
     → Job status updates to "approved"
     → Questions marked "approved", moved into rotation
```

### Workflow 3: Analytics View (Future)
```
Admin → Analytics page
     → Selects: date range, focus key filters
     → Views: % correct by focus key, trap effectiveness, problem questions
     → Identifies: questions with <40% correct, gaps in coverage
     → Action: Click "Review" to go to question detail
```

---

## File Structure

### Backend (Python)
```
backend/app/
├── routers/
│   ├── admin.py (EXISTING, may extend)
│   ├── admin_questions.py (NEW)
│   ├── admin_jobs.py (NEW)
│   └── admin_analytics.py (NEW, Phase 4)
├── models/
│   ├── db.py (MODIFY: verify AdminQuestionAuditLog exists)
│   ├── payload.py (MODIFY: add admin response schemas)
│   └── ontology.py (NO CHANGE)
└── main.py (MODIFY: register new routers)
```

### Frontend (React + TypeScript)
```
FRONTEND/src/
├── pages/
│   └── admin/ (NEW directory)
│       ├── QuestionListPage.tsx
│       ├── QuestionDetailPage.tsx
│       ├── ReviewQueuePage.tsx
│       └── AnalyticsPage.tsx (Phase 4)
├── components/
│   └── admin/ (NEW directory)
│       ├── Sidenav.tsx
│       ├── Header.tsx
│       ├── QuestionTable.tsx
│       ├── QuestionForm.tsx
│       ├── AnnotationPanel.tsx
│       ├── FilterBar.tsx
│       ├── ReviewQueue.tsx
│       ├── JobCard.tsx
│       ├── StatusBadge.tsx
│       ├── Toast.tsx
│       └── ... (10-15 total)
├── api/
│   └── admin/ (NEW directory)
│       ├── questions.ts
│       ├── jobs.ts
│       └── analytics.ts
├── hooks/
│   ├── useQuestions.ts (NEW)
│   ├── useJobs.ts (NEW)
│   └── ... (4-5 total)
├── types/
│   └── admin.ts (NEW)
└── pages/
    └── AdminDashboard.tsx (NEW: root layout)
```

### Tests
```
backend/tests/
└── test_admin_questions.py (NEW)
└── test_admin_jobs.py (NEW)

FRONTEND/src/__tests__/
└── components/admin/
    ├── QuestionTable.test.tsx (NEW)
    ├── QuestionForm.test.tsx (NEW)
    └── ... (5-10 total)
```

---

## API Summary

### Questions Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/questions` | List with filters/pagination |
| GET | `/admin/questions/{id}` | Full detail view |
| POST | `/admin/questions/{id}/edit` | Update question |
| POST | `/admin/questions` | Create new question |
| DELETE | `/admin/questions/{id}` | Soft delete (reject) |

### Jobs/Review Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/jobs` | List jobs by status |
| GET | `/admin/jobs/{id}` | Job detail + questions |
| POST | `/admin/jobs/{job_id}/questions/{q_id}/approve` | Approve single Q |
| POST | `/admin/jobs/{job_id}/questions/{q_id}/reject` | Reject single Q |
| POST | `/admin/jobs/{job_id}/approve` | Approve all in job |

### Analytics Endpoints (Phase 4)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/analytics/performance` | % correct by focus key |
| GET | `/admin/analytics/traps` | Trap effectiveness |
| GET | `/admin/analytics/coverage` | Questions per focus key |

**Full specs in:** `ADMIN_DASHBOARD_DESIGN.md` Section 7

---

## Database Changes

### New Table (if missing)
```sql
CREATE TABLE admin_question_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id UUID NOT NULL REFERENCES questions(id),
  admin_user_id VARCHAR(128) NOT NULL,
  action VARCHAR(50) NOT NULL,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_question_id ON admin_question_audit_logs(question_id);
CREATE INDEX idx_audit_logs_created_at ON admin_question_audit_logs(created_at DESC);
```

### Indexes (verify exist, add if missing)
- `question_annotations.question_id`
- `question_options.question_id`
- `question_jobs.status`
- `questions.practice_status`
- `questions.content_origin`

**No breaking changes to existing tables or schemas.**

---

## Component Complexity Levels

### Simple (1-2 hours)
- StatusBadge — Renders colored status pills
- VersionHistory — Read-only list display
- AuditLog — Read-only log display

### Medium (3-6 hours)
- FilterBar — Collapsible filter controls
- AnnotationPanel — Multi-section read-only display
- JobCard — Collapsible job display with nested questions

### Complex (6-12 hours)
- QuestionTable — Sortable, filterable, paginated data table
- QuestionForm — React Hook Form + validation + error display
- QuestionDetailPage — Coordinate multiple sub-components
- ReviewQueuePage — Manage job list + inline actions

### Very Complex (12+ hours)
- AdminDashboard — Root layout, routing, state management
- AnalyticsPage — Multiple charts, aggregations (Phase 4)

---

## Testing Strategy

### Backend (pytest)
- Unit tests for each endpoint (input validation, DB operations)
- Integration tests for workflows (list → detail → edit → verify)
- E2E tests for approval flow (job load → approve → verify status)
- Fixtures for common test data

**Target:** 95% line coverage, 100% endpoint coverage

### Frontend (Vitest + React Testing Library)
- Component unit tests (rendering, user interactions)
- Hook tests (useQuestions, useEditQuestion)
- Integration tests for page workflows
- Accessibility tests (keyboard nav, screen readers)

**Target:** 80%+ line coverage for critical paths

### Manual QA
- Pagination: Go to page 2, verify data
- Filters: Apply status=approved, verify only approved questions shown
- Edit: Edit question, verify version created
- Approval: Approve from queue, verify status changed
- Error states: Test with invalid input, network errors
- Responsive: Test on mobile (375px), tablet (768px), desktop (1440px)

**Checklist in:** `ADMIN_DASHBOARD_DESIGN.md` Section 8.3

---

## Deployment Checklist

- [ ] Database migrations run (create audit_logs table)
- [ ] Backend routes registered in main.py
- [ ] Backend API tested (Postman or pytest)
- [ ] Frontend built (`npm run build`)
- [ ] Frontend routes configured in React Router
- [ ] Admin JWT auth verified
- [ ] CORS configured (if needed)
- [ ] Error logging configured (Sentry or similar)
- [ ] Monitoring/metrics set up
- [ ] Documentation updated
- [ ] Security audit complete
- [ ] Staging deployment tested
- [ ] Admin team trained on new UI

---

## Known Limitations (MVP)

1. **No real-time updates** — Page requires manual refresh to see changes from other admins
2. **No bulk operations** — Approve/reject must be done per-question (batched in UI, sequential backend)
3. **No advanced filtering** — Only simple field-based filters, no complex queries
4. **No search** — Can't search question text or passage
5. **No reporting** — Analytics dashboard deferred to Phase 4
6. **No vocabulary management UI** — Vocabulary candidates managed via CLI only

**Rationale:** MVP focuses on core workflows, advanced features can iterate separately.

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| List page load | <2s | 25 questions per page, includes pagination |
| Detail page load | <1.5s | Full annotation + all related data |
| Edit form save | <1s | Creates version, logs audit, updates question |
| Approval action | <500ms | Per-question, batch UI |
| Analytics dashboard | <3s | Aggregated queries with caching |

**Optimization strategies:**
- React Query caching (30s stale time)
- Database indexes on frequently queried fields
- Pagination to limit result set size
- Lazy load expandable sections (versions, audit log)

---

## Security Considerations

### Authentication
- All admin routes require `admin_required` decorator
- JWT token validated on each request
- CORS configured to allow only admin origin

### Authorization
- Role-based: only `admin` role can access dashboard
- No direct database access; all through API
- Question edits logged with user ID

### Data Validation
- All inputs validated with Pydantic schemas
- SQL injection prevented by SQLAlchemy ORM
- XSS prevention via React's automatic escaping

### Audit Trail
- Every admin action logged (edit, approve, reject)
- Logs immutable (never deleted)
- Includes user ID, timestamp, action, notes

**Security audit in:** `ADMIN_DASHBOARD_DESIGN.md` Section 9

---

## How to Get Started

### Step 1: Read Design Documents (30 min)
- Read this README first (you are here)
- Skim `ADMIN_DASHBOARD_DESIGN.md` Sections 1-5 (architecture, features)
- Reference `ADMIN_DASHBOARD_WIREFRAMES.md` for UI layout

### Step 2: Understand the API (30 min)
- Review `ADMIN_DASHBOARD_DESIGN.md` Section 7 (API specs)
- Cross-reference with existing admin.py router for patterns
- Understand pagination, filtering, error responses

### Step 3: Backend Development (Week 1)
- Follow `ADMIN_DASHBOARD_TASKS.md` Phase 1 tasks
- Create admin_questions.py and admin_jobs.py routers
- Implement all list/detail/edit endpoints with unit tests
- Test with Postman or pytest

### Step 4: Frontend Development (Week 2-3)
- Follow `ADMIN_DASHBOARD_TASKS.md` Phase 2 tasks
- Create component structure and routing
- Build QuestionListPage and QuestionDetailPage
- Wire up API calls with React Query

### Step 5: Integration & Testing (Week 3-4)
- Follow `ADMIN_DASHBOARD_TASKS.md` Phase 3 tasks
- Add error handling, loading states, responsive design
- Run unit tests (backend + frontend)
- Manual QA on staging

### Step 6: Deploy (Week 4)
- Run database migrations
- Deploy backend + frontend
- Monitor for errors
- Gather admin feedback

---

## Support & Questions

### If you're unclear on:
- **"Why this design?"** → See `ADMIN_DASHBOARD_DESIGN.md` Section 2.2 (Architecture rationale)
- **"What does this component do?"** → See `ADMIN_DASHBOARD_WIREFRAMES.md` Section 2-8
- **"How do I implement X?"** → See `ADMIN_DASHBOARD_TASKS.md` for detailed code stubs
- **"What's the database schema?"** → See `ADMIN_DASHBOARD_DESIGN.md` Section 4.1
- **"How do I test this?"** → See `ADMIN_DASHBOARD_DESIGN.md` Section 8 or `ADMIN_DASHBOARD_TASKS.md` Phase 3.6

### Document Cross-References

```
Design Docs
├─ ADMIN_DASHBOARD_DESIGN.md ←───── "What" & "Why" (features, specs, architecture)
├─ ADMIN_DASHBOARD_WIREFRAMES.md ←─ "How it looks" (layouts, components, responsive)
├─ ADMIN_DASHBOARD_TASKS.md ←────── "How to build" (phases, tasks, code stubs, effort)
└─ This README ←─────────────────── "Quick start" (navigation, decisions, checklist)
```

---

## Deliverables Checklist

### Phase 1: Backend API (Week 1)
- [ ] `admin_questions.py` router with 5 endpoints
- [ ] `admin_jobs.py` router with 6 endpoints
- [ ] Updated `payload.py` with all schemas
- [ ] Updated `db.py` with AdminQuestionAuditLog (if missing)
- [ ] Backend unit tests (pytest)
- [ ] All endpoints tested with Postman

### Phase 2: Frontend Components (Week 2)
- [ ] AdminDashboard root layout
- [ ] Sidenav + Header + routing
- [ ] QuestionListPage + QuestionTable
- [ ] QuestionDetailPage + QuestionForm
- [ ] ReviewQueuePage + JobCard
- [ ] AnnotationPanel + FilterBar
- [ ] API client module (questions.ts, jobs.ts)
- [ ] React Query hooks (useQuestions, useEditQuestion, etc.)
- [ ] TypeScript types (admin.ts)

### Phase 3: Integration & Polish (Week 3)
- [ ] Error handling + Toast notifications
- [ ] Loading states + skeletons
- [ ] Permission checks + redirects
- [ ] Responsive design (mobile/tablet/desktop)
- [ ] Styling + color palette + typography
- [ ] Frontend unit tests (Vitest)
- [ ] Accessibility audit (keyboard nav, ARIA labels)
- [ ] Manual QA checklist (all workflows tested)

### Phase 4: Analytics & Bulk Ops (Week 4, Future)
- [ ] Analytics endpoints (backend)
- [ ] AnalyticsPage + charts
- [ ] BulkOpsPage + reannotate/update workflows
- [ ] Job progress tracking

---

## Success Metrics

**After 3 weeks (MVP), the admin should be able to:**
1. ✓ Login to admin dashboard
2. ✓ View list of questions with filters/pagination
3. ✓ Click question to view full detail with annotation
4. ✓ Edit question (question text, options, explanation)
5. ✓ See version history and audit trail
6. ✓ View job queue with pending approvals
7. ✓ Approve/reject individual questions
8. ✓ Bulk approve/reject entire jobs
9. ✓ All edits logged with admin ID and timestamp

**Metrics:**
- <2s page load time for question list
- 95%+ test coverage (backend)
- 80%+ test coverage (frontend)
- Zero security vulnerabilities
- Admin team adoption >80% within 2 weeks
- Reduces manual review time by 50% vs. raw DB queries

---

## Next Steps

1. **Assign developer:** Choose 1 full-time developer for 3-4 weeks
2. **Setup sprint:** Week 1 = Backend, Week 2 = Frontend, Week 3 = Integration
3. **Daily standups:** 15 min sync on blockers
4. **Code review:** PR review before merging
5. **Staging tests:** Full QA before production deploy

**Timeline: Start Week of [DATE], Deploy by [DATE + 3 WEEKS]**

---

## Document Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-06-18 | v1.0 | Initial design package (4 documents) |

---

**Contact:** For questions or clarifications on this design, reach out to the DSAT team lead.

**Good luck! This is a well-scoped, achievable MVP that will significantly improve admin efficiency.**
