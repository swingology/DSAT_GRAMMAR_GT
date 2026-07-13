# DSAT Admin Dashboard — Wireframes & Component Guide

**Version:** v1.0  
**Date:** 2026-06-18

---

## 1. Layout Overview

### Master Layout (AdminDashboard.tsx)

```
┌─────────────────────────────────────────────────────────────┐
│  DSAT Admin Dashboard                            [Profile ⌄]│
├─────────────────────────────────────────────────────────────┤
│ ▌ Questions  │ Review Queue  │ Analytics  │ Bulk Ops        │
│              │               │            │                 │
├────────────────────────────────────────────────────────────────┤
│                                                              │
│  [PAGE CONTENT - Dynamic based on selected tab]            │
│                                                              │
│                                                              │
└────────────────────────────────────────────────────────────────┘
```

**Sidenav (Fixed, left 250px):**
- Logo / "Admin"
- Tabs: Questions | Review Queue | Analytics | Bulk Ops
- User info (name, email)
- Logout

**Header (Fixed, top 60px):**
- Breadcrumb or page title
- Quick search (optional)
- Notifications badge (job status)

**Content Area (Fluid):**
- Scrollable, margins 24px
- Responsive to mobile (<768px → collapse sidenav)

---

## 2. Question List Page

### Wireframe: QuestionListPage.tsx

```
╔════════════════════════════════════════════════════════════════╗
║  Questions                                 [+ Create Question] ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Filters: [Status ▼] [Origin ▼] [Test ▼] [Focus Key ▼]       ║
║           [Date from ___] [Date to ___]          [Search ___] ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  ☐  ID            Test        Q#  Status      % Correct   ...  ║
╟────────────────────────────────────────────────────────────────╢
║  ☑  qid-abc123   Test 1       1   ✓ Approved  78%         [...]║
║  ☐  qid-def456   Test 4       5   ⊙ Draft     65%         [...]║
║  ☐  qid-ghi789   Test 5      10   ✕ Rejected  52%         [...]║
║  ☐  qid-jkl012   Test 1       2   ✓ Approved  81%         [...]║
║  ☐  qid-mno345   Test 10      8   ⊙ Draft     —           [...]║
║                                                                ║
║  [← Prev] Page 1 of 18 [1 2 3 4 ... 18] [Next →]            ║
║  Showing 1-25 of 450 questions                              ║
╚════════════════════════════════════════════════════════════════╝
```

**Columns:**
1. Checkbox (bulk select)
2. Question ID (link to detail)
3. Test name
4. Question number
5. Status badge
6. % correct (from user progress)
7. Last modified (date)
8. Actions (ellipsis menu → Edit, Copy, Delete)

**Filters (Collapsible Row):**
- Status: [Draft] [Approved] [Rejected] (multiselect)
- Origin: [Official] [Generated]
- Test: (dropdown, populated from DB)
- Focus Key: (dropdown)
- Date range: From __ To __
- Free text search: (searches question_text)
- [Apply] [Reset] buttons

**Actions:**
- Click row → Navigate to detail page
- Bulk select + "Approve All" / "Reject All" buttons (appears on selection)
- "Create Question" button (top right, opens modal)

---

## 3. Question Detail Page

### Wireframe: QuestionDetailPage.tsx

```
╔════════════════════════════════════════════════════════════════╗
║  Question #1 from Test 1                    [← Back] [Edit v]  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  STATUS: ✓ Approved (by admin, 2026-06-18)                   ║
║  ORIGIN: official  |  TEST: Test 1  |  Q#: 1                 ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  QUESTION                                                      ║
║  ────────────────────────────────────────────────────────────  ║
║  The quick brown fox jumps over the lazy dog, which _____ the  ║
║  fence. [in bold: underlined text here]                       ║
║                                                                ║
║  PASSAGE                                                       ║
║  ────────────────────────────────────────────────────────────  ║
║  In the beginning, there was nothing. The world slowly formed  ║
║  from chaos into order...  [truncated, expandable]            ║
║                                                                ║
║  OPTIONS                                                       ║
║  ────────────────────────────────────────────────────────────  ║
║  (A)  is leaping over    [trap: auxiliary_verb_omission]      ║
║  (B)  leap over          [correct]                            ║
║  (C)  leaps over the     [trap: subject_verb_mismatch]        ║
║  (D)  had leaped over    [distractor: wrong tense]            ║
║                                                                ║
║  EXPLANATION                                                   ║
║  ────────────────────────────────────────────────────────────  ║
║  Option B is correct because the subject "fox" is singular... ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  ANNOTATION (READ-ONLY)                                        ║
║  ────────────────────────────────────────────────────────────  ║
║                                                                ║
║  Grammar Focus Keys:  [subject_verb_agreement] [verb_form]    ║
║  Trap Keys:          [auxiliary_verb_omission]               ║
║  Syntactic Traps:    [shows per-option breakdown]            ║
║                                                                ║
║  Confidence Scores:                                            ║
║  ├─ Overall:      ████████░ 92%                              ║
║  ├─ Focus Key:    █████████ 95%                              ║
║  └─ Traps:        ███████░░ 88%                              ║
║                                                                ║
║  Distractor Analysis (Expanded):                              ║
║  ┌──────┬────────────┬──────────────┬──────────────┐         ║
║  │ Opt  │ Role       │ Why Plausible│ Why Wrong    │         ║
║  ├──────┼────────────┼──────────────┼──────────────┤         ║
║  │ A    │ trap       │ Native spkrs │ Grammar rule │         ║
║  │      │            │ drop aux...  │ requires aux │         ║
║  │ B    │ correct    │ —            │ —            │         ║
║  │ C    │ trap       │ Plural form  │ S-V mismatch │         ║
║  │      │            │ in passage.. │ with singular│         ║
║  │ D    │ distractor │ Plausible    │ Wrong tense  │         ║
║  │      │            │ wrong tense  │ doesn't fit  │         ║
║  └──────┴────────────┴──────────────┴──────────────┘         ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  VERSION HISTORY                                               ║
║  ────────────────────────────────────────────────────────────  ║
║  v1 (2026-05-01, ingestion)      [View] [Restore]            ║
║  v2 (2026-06-10, admin edit)     [View] [Restore]            ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  AUDIT LOG                                                     ║
║  ────────────────────────────────────────────────────────────  ║
║  2026-06-18 10:30 — admin1 — APPROVED — "Good traps"        ║
║  2026-06-10 14:05 — admin2 — EDITED — "Clarified wording"   ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║  [Edit] [Approve] [Reject] [Mark Review] [Delete]            ║
╚════════════════════════════════════════════════════════════════╝
```

**Sections (Collapsible):**
1. **Header:** Status badge, metadata (origin, test, Q#)
2. **Question Content:** Question text, passage (expandable), options, explanation
3. **Annotation Panel:** Focus keys, traps, confidence scores, distractor analysis
4. **Version History:** List of past versions with view/restore
5. **Audit Log:** Admin actions on this question
6. **Action Buttons:** Edit, Approve, Reject, Mark for Review, Delete

**Color Coding:**
- Status badge: Green (approved), Orange (draft), Red (rejected)
- Trap indicators: Red pills for trap keys, Blue pills for focus keys
- Confidence bars: Green >80%, Yellow 50-80%, Red <50%

---

## 4. Question Edit Modal

### Wireframe: QuestionForm.tsx (within QuestionDetailPage or separate modal)

```
╔════════════════════════════════════════════════════════════════╗
║  Edit Question                                        [✕ Close]║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Question Text *                                               ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ The quick brown fox jumps over the lazy dog, which     │  ║
║  │ _____ the fence.                                       │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  Passage Text (optional)                                       ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ In the beginning, there was nothing...                 │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  Options *                                                     ║
║  ┌──────────────────────────────────────────────────────┐    ║
║  │ Label │ Text                      │ Correct │ Delete │    ║
║  ├──────────────────────────────────────────────────────┤    ║
║  │  A    │ is leaping over           │ ☐       │  [✕]  │    ║
║  │  B    │ leap over                 │ ⦿       │  [✕]  │    ║
║  │  C    │ leaps over the            │ ☐       │  [✕]  │    ║
║  │  D    │ had leaped over           │ ☐       │  [✕]  │    ║
║  └──────────────────────────────────────────────────────┘    ║
║                                                                ║
║  Explanation *                                                 ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ Option B is correct because the subject "fox" is...   │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  Change Notes (optional)                                       ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ Clarified the wording of option C to reduce ambiguity │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  [Cancel]  [Save Draft]  [Save & Close]                      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Form Fields:**
1. **Question Text** (required, textarea, ~100 chars typical)
2. **Passage Text** (optional, textarea, can be long)
3. **Options** (required, 4 rows: label, text, is_correct radio)
4. **Explanation** (required, textarea)
5. **Change Notes** (optional, free text for audit trail)

**Validation:**
- Question text not empty
- Exactly one correct answer selected
- All options have non-empty text
- Explanation not empty

**Buttons:**
- Cancel (discard changes)
- Save Draft (saves without closing)
- Save & Close (saves and returns to detail)

---

## 5. Review Queue Page

### Wireframe: ReviewQueuePage.tsx

```
╔════════════════════════════════════════════════════════════════╗
║  Review Queue — Pending Approval                              ║
╠════════════════════════════════════════════════════════════════╣
║  Filter: [All] [Needs Review] [Failed] [Last 24h]            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌───────────────────────────────────────────────────────┐   ║
║  │ Job: Official Grammar Ingestion                       │   ║
║  │ ID: job-abc123                                        │   ║
║  │ Status: ⚠ Needs Review                              │   ║
║  │ Questions: 27 / 27                                   │   ║
║  │ Errors: qnum_ocr_crosscheck (2 items)               │   ║
║  │ Triggered: 2026-06-18 08:00 UTC                      │   ║
║  ├───────────────────────────────────────────────────────┤   ║
║  │ Q#1: "The quick brown..." [⚠ qnum mismatch]         │   ║
║  │      [Approve] [Reject ▼]  [View Full]              │   ║
║  │                                                       │   ║
║  │ Q#2: "In the beginning..." [✓ OK]                   │   ║
║  │      [Approve] [Reject ▼]  [View Full]              │   ║
║  │                                                       │   ║
║  │ Q#3: "The author states..." [⚠ qnum mismatch]       │   ║
║  │      [Approve] [Reject ▼]  [View Full]              │   ║
║  │                                                       │   ║
║  │                                                       │   ║
║  │ [↑ Load more] (20/27 visible)                        │   ║
║  ├───────────────────────────────────────────────────────┤   ║
║  │ Bulk Actions:                                         │   ║
║  │ [Approve All] [Reject All] [Mark for Manual Review]  │   ║
║  └───────────────────────────────────────────────────────┘   ║
║                                                                ║
║  ┌───────────────────────────────────────────────────────┐   ║
║  │ Job: Generated Practice Set #42                       │   ║
║  │ ID: job-def456                                        │   ║
║  │ Status: ⚠ Needs Review (3 errors)                   │   ║
║  │ Questions: 15 / 15                                   │   ║
║  │ Errors: missing_annotation (3)                       │   ║
║  │ Triggered: 2026-06-17 16:30 UTC                      │   ║
║  ├───────────────────────────────────────────────────────┤   ║
║  │ [Approve All] [Reject All]                           │   ║
║  └───────────────────────────────────────────────────────┘   ║
║                                                                ║
║  Page 1 of 2  [Next →]                                       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Job Card Components:**
1. **Header:** Job type, ID, status badge, question count
2. **Error Summary:** List of validation errors (if any)
3. **Timestamp:** When job was triggered
4. **Inline Question Preview:** First 20 questions, with issue badges
5. **Quick Actions per Question:** Approve, Reject (dropdown), View Full
6. **Bulk Actions:** Approve All, Reject All for entire job

**Status Badges:**
- ✓ Approved (green)
- ⚠ Needs Review (orange)
- ✕ Failed (red)
- ⊙ In Progress (blue spinner)

**Error Types:**
- qnum_ocr_crosscheck (question number mismatch)
- missing_annotation (annotation failed)
- invalid_options (fewer than 4 options)

---

## 6. Reject Modal

### Wireframe: ApprovalModal.tsx

```
╔════════════════════════════════════════════════════════════════╗
║  Reject Question                                    [✕ Cancel] ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  Are you sure you want to reject this question?               ║
║                                                                ║
║  Question: "The quick brown fox..."                           ║
║                                                                ║
║  Reason (required) *                                           ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │                                                        │  ║
║  │ [✓] Traps too obvious                                 │  ║
║  │ [✓] Grammar rules incorrect                           │  ║
║  │ [ ] Spelling/typo error                               │  ║
║  │ [ ] Inappropriate content                             │  ║
║  │ [ ] Duplicate of another question                     │  ║
║  │ [ ] Other (please specify)                            │  ║
║  │                                                        │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  Additional Notes                                              ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ Option A is too similar to Option C                  │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  [Cancel]  [Reject Question]                                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Form:**
- Reason selection (checkboxes, allow multiple)
- Additional notes (textarea)
- Confirm/Cancel buttons

---

## 7. Analytics Dashboard

### Wireframe: AnalyticsPage.tsx

```
╔════════════════════════════════════════════════════════════════╗
║  Analytics Dashboard                                          ║
╠════════════════════════════════════════════════════════════════╣
║  Date Range: [Last 7 days ▼] | Focus Key: [All ▼]           ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌──────────────────┐  ┌──────────────────┐                  ║
║  │ Questions        │  │ Total Attempts   │                  ║
║  │ 450              │  │ 12,340           │                  ║
║  │ (↑12 this week)  │  │ (↑2,100 this w)  │                  ║
║  └──────────────────┘  └──────────────────┘                  ║
║                                                                ║
║  ┌──────────────────┐  ┌──────────────────┐                  ║
║  │ Avg % Correct    │  │ Identified Gaps  │                  ║
║  │ 72%              │  │ 8 focus keys     │                  ║
║  │ (↑2pts vs month) │  │ need more Qs     │                  ║
║  └──────────────────┘  └──────────────────┘                  ║
║                                                                ║
║  PERFORMANCE BY FOCUS KEY                                     ║
║  ┌─────────────────────────────────────┬────────────┐        ║
║  │ Focus Key                           │ % Correct  │        ║
║  ├─────────────────────────────────────┼────────────┤        ║
║  │ subject_verb_agreement              │ ████████░░ 82%     │        ║
║  │ verb_form                           │ ███████░░░ 70%     │        ║
║  │ comma_usage                         │ ██████░░░░ 60%     │        ║
║  │ pronoun_antecedent_agreement        │ █████░░░░░ 50%     │        ║
║  │ parallel_structure                  │ ███░░░░░░░ 30%     │        ║
║  └─────────────────────────────────────┴────────────┘        ║
║                                                                ║
║  TOP TRAPS (Most Effective Distractors)                       ║
║  ┌──────────────────────┬────────┬───────────┐               ║
║  │ Trap Key             │ % Sel  │ Q Count   │               ║
║  ├──────────────────────┼────────┼───────────┤               ║
║  │ auxiliary_verb_omit  │ 42%    │ 12        │               ║
║  │ tense_mismatch       │ 38%    │ 8         │               ║
║  │ s_v_mismatch         │ 35%    │ 15        │               ║
║  │ pronoun_case_wrong   │ 28%    │ 10        │               ║
║  └──────────────────────┴────────┴───────────┘               ║
║                                                                ║
║  QUESTIONS NEEDING ATTENTION (< 40% correct)                 ║
║  ┌──────────────────────────────────┬────────────┬──────┐    ║
║  │ Question ID                      │ % Correct  │ Attn │    ║
║  ├──────────────────────────────────┼────────────┼──────┤    ║
║  │ qid-jkl012 (Test 1, Q#5)         │ 18%        │ 🔴   │    ║
║  │ qid-xyz789 (Test 4, Q#12)        │ 22%        │ 🔴   │    ║
║  │ qid-pqr456 (Test 7, Q#8)         │ 38%        │ 🟠   │    ║
║  └──────────────────────────────────┴────────────┴──────┘    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Sections:**
1. **KPI Cards** (top): Total questions, attempts, avg % correct, identified gaps
2. **Performance Table** (by focus key): Bar chart + % correct
3. **Trap Effectiveness** (most effective traps): % selected, question count
4. **Problem Questions** (lowest performers): ID, % correct, flag for review

---

## 8. Bulk Operations Page

### Wireframe: BulkOpsPage.tsx

```
╔════════════════════════════════════════════════════════════════╗
║  Bulk Operations                                              ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  RE-ANNOTATE QUESTIONS                                         ║
║  ────────────────────────────────────────────────────────────  ║
║  Select questions to re-run annotation pipeline:              ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ Filter by focus key: [All ▼]                          │  ║
║  │ Filter by status:    [All ▼]                          │  ║
║  │ [Apply Filter]                                        │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  Selected: 12 questions (from 450)                            ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ ☑ qid-abc123 (Test 1, Q#1)      [✓]                  │  ║
║  │ ☑ qid-def456 (Test 1, Q#2)      [✓]                  │  ║
║  │ ☑ qid-ghi789 (Test 1, Q#5)      [⚠]                  │  ║
║  │                                                        │  ║
║  │ [Prev] Page 1 of 1 [Next]                             │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  [Cancel] [Start Re-Annotation Job]                          ║
║                                                                ║
║  ────────────────────────────────────────────────────────────  ║
║                                                                ║
║  RECENT JOB HISTORY                                            ║
║  ────────────────────────────────────────────────────────────  ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ Job: Reannotate Q selection (focus_key=verb_form)     │  ║
║  │ ID: job-re-abc123                                     │  ║
║  │ Status: ✓ Completed (2026-06-18 10:30 UTC)           │  ║
║  │ Questions: 12 / 12                                   │  ║
║  │ Result: 12 updated, 0 failed                         │  ║
║  │ [View Details]                                        │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ Job: Reannotate Q selection (focus_key=subject_verb)  │  ║
║  │ ID: job-re-def456                                     │  ║
║  │ Status: ⊙ In Progress (50% - 6/12)...               │  ║
║  │ Questions: 12 total                                  │  ║
║  │ Current: Processing q-xyz789...                      │  ║
║  │ [View Details]                                        │  ║
║  └────────────────────────────────────────────────────────┘  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

**Sections:**
1. **Selection Interface:** Filter + paginated list with checkboxes
2. **Action Buttons:** Start bulk operation
3. **Job History:** List of past/ongoing jobs with status and progress

**Status Indicators:**
- ✓ Completed
- ⊙ In Progress (with %)
- ✕ Failed

---

## 9. Component Hierarchy

```
AdminDashboard (root layout)
├── Sidenav
│   ├── Logo
│   ├── Navigation Tabs
│   └── User Info
├── Header
│   ├── Breadcrumb
│   ├── Title
│   └── Notifications Badge
└── Content Area (dynamic)
    ├── QuestionListPage
    │   ├── FilterBar
    │   ├── QuestionTable
    │   │   └── QuestionRow (×25)
    │   └── Pagination
    │
    ├── QuestionDetailPage
    │   ├── StatusBar
    │   ├── QuestionDisplay
    │   ├── AnnotationPanel
    │   │   └── DistractorAnalysisTable
    │   ├── VersionHistory
    │   ├── AuditLog
    │   └── ActionButtons
    │       └── QuestionForm (modal on Edit)
    │
    ├── ReviewQueuePage
    │   ├── FilterBar
    │   ├── JobCard (×N)
    │   │   ├── JobHeader
    │   │   ├── ErrorSummary
    │   │   ├── QuestionPreviewList (×20)
    │   │   │   └── QuestionRow (inline)
    │   │   └── BulkActionButtons
    │   └── Pagination
    │
    ├── AnalyticsPage
    │   ├── DateRangeSelector
    │   ├── KPICards (4)
    │   ├── PerformanceTable
    │   ├── TrapEffectivenessTable
    │   └── ProblemQuestionsTable
    │
    └── BulkOpsPage
        ├── ReAnnotateSection
        │   ├── FilterBar
        │   ├── QuestionPreviewList
        │   └── ActionButtons
        └── JobHistorySection
            └── JobCard (×N)
```

---

## 10. Color Palette & Icons

### Status Badges
- **Approved:** Green (#10B981) with ✓
- **Draft:** Gray (#9CA3AF) with ⊙
- **Rejected:** Red (#EF4444) with ✕
- **Needs Review:** Orange (#F97316) with ⚠
- **In Progress:** Blue (#3B82F6) with ⊙ spinner

### Text Colors
- **Primary:** #1F2937 (dark gray)
- **Secondary:** #6B7280 (medium gray)
- **Muted:** #9CA3AF (light gray)
- **Error:** #EF4444 (red)
- **Success:** #10B981 (green)
- **Warning:** #F97316 (orange)

### Icons
- ✓ Checkmark (approved)
- ✕ X mark (rejected, delete)
- ⚠ Warning triangle (needs review)
- ⊙ Spinning circle (in progress)
- 🔍 Magnifying glass (search)
- 🔗 Link (open detail)
- ⋮ Ellipsis (more actions)
- ↓ Chevron down (expand)
- ← Chevron left (back)
- → Chevron right (next)

### Tailwind Classes (Quick Ref)
```tsx
// Buttons
className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"

// Cards
className="border border-gray-200 rounded-lg p-6 shadow-sm"

// Badges
className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800"

// Tables
className="min-w-full divide-y divide-gray-200"

// Forms
className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500"
```

---

## 11. Responsive Design Breakpoints

| Breakpoint | Screen Width | Behavior |
|---|---|---|
| Mobile | <640px | Sidenav collapses to hamburger menu; tables stack vertically |
| Tablet | 640px - 1024px | Sidenav pinned, reduced width; tables scroll horizontally |
| Desktop | >1024px | Full sidenav; tables use full width |

**Example Mobile Layout:**
```
┌──────────────────┐
│ ☰ Questions     │
├──────────────────┤
│ [Filter]        │
├──────────────────┤
│ Q1: "The quick" │
│ Status: Approved│
│ % Correct: 78%  │
├──────────────────┤
│ Q2: "In the...  │
│ Status: Draft   │
│ % Correct: 65%  │
├──────────────────┤
│ [Next Page]     │
└──────────────────┘
```

---

## 12. Data Display Examples

### Question Preview (Compact)
```
Q#1: "The quick brown fox _____ the fence."
Status: ✓ Approved  |  Correct: 78%  |  Attempts: 127
Options: A) is leaping  B) leap  C) leaps  D) had leaped
```

### Option Display (Full)
```
(B)  leap over
     Role: correct
     Distractor Type: —
     Why Plausible: —
     Why Wrong: —
     Grammar Fit: —
```

### Confidence Score Display
```
Overall Confidence:      ████████░ 92%
Focus Key Confidence:    █████████ 95%
Trap Identification:     ███████░░ 88%
Option Quality:          ██████░░░ 60%
```

---

## 13. User Flow Diagrams

### Approval Workflow
```
Job Queue Page
  → Click "Review All" on job
    → Job Detail Page (see all 27 Qs)
      → For each question:
         → Check annotation & traps
         → [Approve] → Q marked approved, move to next
         → [Reject] → Modal with reason → Q rejected, move to next
      → Bulk action options: Approve All remaining, Reject All
    → Back to queue (job shows status updated)
```

### Question Edit Workflow
```
Question List
  → Click question row
    → Question Detail Page
      → [Edit] button
        → Question Form modal opens
          → Edit question text, options, explanation
          → [Save & Close]
        → New QuestionVersion created in DB
        → Annotation marked as stale (if needed)
        → Audit log entry added
    → Back to detail (updated content shown)
```

---

## 14. Accessibility Requirements

- **Keyboard Navigation:** Tab through all interactive elements
- **Screen Readers:** ARIA labels on buttons, form fields
- **Color Contrast:** WCAG AA compliant (4.5:1 for text)
- **Focus Indicators:** Visible on all buttons/links
- **Form Validation:** Clear error messages below fields
- **Icon Labeling:** All icons have text alternative or title attr

**Example:**
```tsx
<button 
  aria-label="Approve this question"
  title="Approve (A)"
  className="... focus:ring-2 focus:ring-offset-2"
>
  <CheckIcon className="w-4 h-4" />
</button>
```

---

## 15. States & Transitions

### Button States
```
Default:    [Button text] ← clickable
Hover:      [Button text] ← bg slightly darker
Active:     [Button text] ← bg darker, shadow
Disabled:   [Button text] ← grayed out, cursor: not-allowed
Loading:    [⊙ Processing...] ← spinner + text
Success:    [✓ Done] ← green background (2s then revert)
Error:      [✕ Error] ← red background + error message below
```

### Form Field States
```
Default:    |____________________| 
Focused:    |____________________| ← blue border, shadow
Filled:     |Text entered...........| ← filled state
Error:      |____________________| ← red border
            Error message here
Success:    |____________________| ← green border
            ✓ All good
```

### Table Row States
```
Default:    | ☐ | Q#1 | Status | ... |
Hover:      | ☐ | Q#1 | Status | ... | ← gray background
Selected:   | ☑ | Q#1 | Status | ... | ← checkbox checked, highlight
Loading:    | ⊙ | Q#1 | Status | ... | ← spinner in first column
```

---

## 16. Typography

- **H1 (Page Title):** 28px, bold, #1F2937
- **H2 (Section Title):** 20px, bold, #1F2937
- **H3 (Card Title):** 16px, bold, #374151
- **Body:** 14px, regular, #4B5563
- **Small:** 12px, regular, #6B7280
- **Monospace (code):** Monaco/Courier, 12px, #1F2937

---

This wireframe document is a visual guide for developers to reference while implementing components. All examples use simple ASCII art to show layout and hierarchy, not pixel-perfect designs.
