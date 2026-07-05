# Student Tracking Backend — Implementation Audit

## Executive Summary

**Status:** ~65% of required infrastructure already exists in the database and API.

The backend already has excellent trap/distractor tracking in place at the question option level. The primary gap is aggregating this data into student profiles and providing analytics endpoints.

---

## Database Audit

### ✅ Already Exists

#### 1. UserProgress Table (Fully Ready)
**Location:** `backend/app/models/db.py:494`

**Current Schema:**
```python
class UserProgress(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID, ForeignKey("questions.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    selected_option_label = Column(String(1), nullable=False)
    
    # 🎯 TRAP DATA ALREADY HERE:
    missed_grammar_focus_key = Column(String(50), nullable=True)
    missed_syntactic_trap_key = Column(String(50), nullable=True)  # ← THIS IS THE TRAP TYPE
    missed_reading_focus_key = Column(String(100), nullable=True)
    missed_reading_skill_family_key = Column(String(100), nullable=True)
    
    # METADATA:
    question_domain = Column(String(20), nullable=True, index=True)
    question_difficulty = Column(String(20), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, index=True)
    
    # 📊 INDEXES for performance:
    Index("ix_user_progress_user_id", "user_id")
    Index("ix_user_progress_question_id", "question_id")
```

**Reuse Impact:** 
- ✅ Every answer already records `missed_syntactic_trap_key`
- ✅ Already indexed by user_id for fast queries
- ✅ Timestamp auto-tracked
- ✅ Can directly aggregate to build student susceptibility profiles

---

#### 2. QuestionOption Table (Rich Distractor Metadata)
**Location:** `backend/app/models/db.py:167`

**Current Schema:**
```python
class QuestionOption(Base):
    id = Column(UUID, primary_key=True)
    question_id = Column(UUID, ForeignKey("questions.id"), nullable=False)
    option_label = Column(String(1), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    
    # 🎯 DISTRACTOR TRAP METADATA:
    distractor_type_key = Column(String(100), nullable=True)  # "subject_number_mismatch", etc.
    semantic_relation_key = Column(String(100), nullable=True)
    plausibility_source_key = Column(String(100), nullable=True)
    option_error_focus_key = Column(String(100), nullable=True)
    student_failure_mode_key = Column(String(100), nullable=True)  # ← Error psychology
    
    # 📊 TRAP EFFECTIVENESS METRICS:
    distractor_distance = Column(String(50), nullable=True)  # How far from correct
    distractor_competition_score = Column(Float, nullable=True)  # How competitive (0-1)
    
    # QUALITY INDICATORS:
    why_plausible = Column(Text, nullable=True)  # Why this trap works
    why_wrong = Column(Text, nullable=True)      # Why it's actually wrong
    grammar_fit = Column(String(3), nullable=True)
    tone_match = Column(String(3), nullable=True)
    precision_score = Column(SmallInteger, nullable=True)
```

**Reuse Impact:**
- ✅ Every option already has distractor classification
- ✅ Each trap has a `distractor_type_key` identifier
- ✅ Why explanations already present
- ✅ Can be joined with UserProgress to understand which traps triggered

---

#### 3. Question Table (Question Type Classification)
**Location:** `backend/app/models/db.py:69`

**Current Fields:**
```python
class Question(Base):
    # 📚 CLASSIFICATION:
    stimulus_mode_key = Column(String(100), nullable=True)
    stem_type_key = Column(String(100), nullable=True)
    
    # 🔗 ANNOTATION LINKAGE:
    latest_annotation_id = Column(UUID, ForeignKey("question_annotations.id"), nullable=True)
    latest_version_id = Column(UUID, ForeignKey("question_versions.id"), nullable=True)
    
    # 📊 RELATIONSHIPS (for eager loading):
    annotations = relationship("QuestionAnnotation", ...)
    options = relationship("QuestionOption", ...)  # ← Can join to get all distractors
```

**Reuse Impact:**
- ✅ Has relationships to annotations and options
- ✅ Can follow latest_annotation_id → QuestionAnnotation.annotation_jsonb for full metadata
- ✅ Indexed on latest_annotation_id

---

#### 4. QuestionAnnotation Table (Comprehensive Metadata)
**Location:** `backend/app/models/db.py:148`

**Current Schema:**
```python
class QuestionAnnotation(Base):
    id = Column(UUID, primary_key=True)
    question_id = Column(UUID, ForeignKey("questions.id"), nullable=False)
    question_version_id = Column(UUID, ForeignKey("question_versions.id"), nullable=False)
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    
    # 🎯 THE KEY FIELD - Contains all question metadata:
    annotation_jsonb = Column(JSONB, nullable=False, default=dict)
    explanation_jsonb = Column(JSONB, nullable=False, default=dict)
    generation_profile_jsonb = Column(JSONB, nullable=True)
    confidence_jsonb = Column(JSONB, nullable=False, default=dict)
```

**What's in annotation_jsonb:**
(From analysis of payload schemas)
- `grammar_focus_key` — e.g., "subject_verb_agreement"
- `grammar_role_key` — e.g., "parts_of_speech"
- `syntactic_trap_key` — e.g., "subject_number_mismatch"
- `reading_focus_key` — e.g., "evidence_supports_claim"
- `reading_skill_family_key` — e.g., "command_of_evidence_textual"
- `difficulty_overall` — difficulty assessment
- Additional context fields

**Reuse Impact:**
- ✅ All question type classification already stored
- ✅ All trap identification already recorded
- ✅ Can be queried via JSONB operators
- ✅ Indexed on question_id for fast lookup

---

### ❌ Needs to Be Created

#### 1. StudentTrapSusceptibility Table
**Purpose:** Aggregated student profile on trap susceptibility

**Reason for New Table:** 
- Denormalize for fast dashboard queries
- Nightly aggregation of UserProgress data
- Track improvement trends per trap

**Proposed Schema:**
```sql
CREATE TABLE student_trap_susceptibility (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Per-trap metrics (JSONB for flexibility):
    trap_fall_rates JSONB,  -- {"subject_number_mismatch": 0.72, ...}
    trap_improvement JSONB, -- {"tense_consistency": {"old": 0.3, "new": 0.6}, ...}
    trap_patterns JSONB,    -- {trap_type: {occurrences, recent_accuracy}}
    
    -- Rankings:
    most_susceptible_traps VARCHAR[] DEFAULT ARRAY[]::VARCHAR[],
    overcoming_traps VARCHAR[],
    persistent_traps VARCHAR[],
    
    -- Metadata:
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_susceptibility UNIQUE (user_id),
    INDEX idx_user_id (user_id)
);
```

#### 2. DiagnosticSession Table (From Phase 1)
**See Phase 1 PRD section for full schema**

**Connection to Trap Analysis:**
```
DiagnosticSession
├── question_ids UUID[]
└── Each question's trap data available via:
    └── UserProgress.missed_syntactic_trap_key → Can aggregate trap triggers
```

#### 3. StudentDailyStats / StudentWeeklyStats (From Phase 3)
**See Phase 3 PRD section**

**Enhancement for Trap Analysis:**
```sql
-- Add to student_daily_stats:
trap_focus_stats JSONB,  -- {trap_type: {attempts, correct, fall_rate}}

-- Add to student_weekly_stats:
trap_improvement_trend JSONB  -- {trap: improvement_rate}
```

---

## API Endpoints Audit

### ✅ Already Implemented

#### 1. POST /api/submit
**Location:** `backend/app/routers/student.py:474`

**Current Signature:**
```python
@router.post("/submit")
async def submit_answer(
    body: UserProgressCreate,  # Contains selected_option_label
    db: AsyncSession,
    _auth: str = Depends(student_required),
)
```

**What It Does:**
```python
# From the endpoint (lines 474-556):
is_correct = q.current_correct_option_label == body.selected_option_label

# Stores:
progress = UserProgress(
    user_id=user.id,
    question_id=qid,
    is_correct=is_correct,
    selected_option_label=body.selected_option_label,
    missed_grammar_focus_key=body.missed_grammar_focus_key or ann_data.get("grammar_focus_key"),
    missed_syntactic_trap_key=body.missed_syntactic_trap_key,  # ← Can be passed from frontend
    missed_reading_focus_key=...,
    missed_reading_skill_family_key=...,
    question_domain=question_domain,  # auto-computed
    question_difficulty=question_difficulty,  # auto-computed
)
```

**Reuse Impact:**
- ✅ Already stores `missed_syntactic_trap_key`
- ✅ Validates question exists and is active
- ✅ Performs correctness check
- ⚠️ **Missing:** Frontend doesn't pass `missed_syntactic_trap_key`
  - Solution: Update frontend to extract trap type from selected option and pass it

#### 2. GET /api/study/recommendations
**Location:** `backend/app/routers/student.py:1212`

**Current Returns:**
```python
response_model=StudyRecommendationsResponse

{
  "top_targets": [
    {
      "focus_key": "subject_verb_agreement",
      "domain": "grammar",
      "miss_rate": 0.45,
      "missed_count": 18,
      "attempted_count": 40
    }
  ]
}
```

**Reuse Impact:**
- ✅ Already calculates miss rates by focus area
- ✅ Can be extended to calculate by trap type
- ✅ Backend logic already analyzes `missed_grammar_focus_key`

#### 3. GET /api/study/missed
**Location:** `backend/app/routers/student.py:1417`

**Current Returns:**
```python
response_model=MissedQuestionsResponse

{
  "items": [
    {
      "question_id": "uuid",
      "domain": "grammar",
      "focus_key": "subject_verb_agreement",
      "user_answer": "A",
      "correct_answer": "B",
      "explanation": "...",
      "miss_count": 3,
      "last_missed_at": "2024-06-20T..."
    }
  ]
}
```

**Reuse Impact:**
- ✅ Already tracks which questions user missed
- ✅ Can be extended to include `trap_type` from selected option
- ✅ Query logic can group by trap type instead of focus key

---

### ❌ Needs to Be Implemented

#### Endpoints to Add (New)

1. **GET /api/student/trap-susceptibility**
   - Query: `SELECT missed_syntactic_trap_key, COUNT(*), SUM(is_correct) FROM user_progress WHERE user_id = ? GROUP BY missed_syntactic_trap_key`
   - Enhance: Join with QuestionOption to get trap metadata
   - Serve: student_trap_susceptibility table (nightly aggregation)

2. **GET /api/student/question-type-performance**
   - Query: Question.stem_type_key + accuracy
   - Enhance: Group by grammatical/reading type
   - Serve: Breakdown of accuracy per question type

3. **GET /api/student/trap-details/{trap_type}**
   - Query: All questions with this trap_type
   - Enhance: Filter to ones user has attempted
   - Serve: Examples, definitions, user history

4. **POST /api/study/recommendations/trap-focused**
   - Extension of `/study/recommendations`
   - Filter to questions with recommended traps
   - Serve: Targeted practice sets

---

## Data Flow Mapping

### Current Flow (Partial)
```
Frontend Answer Selection
    ↓
POST /api/submit
    ↓ (stores)
UserProgress
    ├── question_id → Question.latest_annotation_id → annotation_jsonb
    ├── selected_option_label → QuestionOption.distractor_type_key
    └── is_correct (computed)
    
Backend Computes:
    - is_correct (from question.current_correct_option_label)
    - question_domain (from annotation)
    - question_difficulty (from annotation)
    - missed_grammar_focus_key (from annotation or frontend param)
    - ❌ missed_syntactic_trap_key (stored but NOT populated by frontend)
```

### Enhanced Flow (Proposed)
```
Frontend Answer Selection
    ↓
Determine Trap Type:
  - selected_option → QuestionOption.distractor_type_key
  - or: question.latest_annotation → syntactic_trap_key
    ↓
POST /api/submit (with trap_type)
    ↓ (stores)
UserProgress + trap data
    ├── missed_syntactic_trap_key = extracted trap type
    └── timestamp
    
Nightly Batch Job:
  ↓
StudentTrapSusceptibility Aggregation:
  - COUNT per trap_type
  - SUM(is_correct) per trap_type
  - Calculate fall_rate = 1 - (correct_sum / count)
  - Identify top 5 traps
  - Detect improvement trends
    ↓
GET /api/student/trap-susceptibility
    ↓
Dashboard Display
```

---

## Implementation Priority

### 🟢 Phase 2.5 - Tier 1 (Can Start Immediately)

**No Schema Changes Needed:**

1. **Frontend Enhancement**
   - Extract `distractor_type_key` from selected QuestionOption
   - Pass `missed_syntactic_trap_key` to `/api/submit`
   - Cost: ~1-2 days
   - Unblocks: Everything else

2. **Endpoint: GET /api/student/trap-susceptibility**
   - Query UserProgress directly (no new table yet)
   - Aggregate on-the-fly for now
   - Cost: ~1 day
   - Performance: OK for small user base, needs caching after

3. **Dashboard Component**
   - StudentTrapSusceptibilityDashboard
   - Calls `/api/student/trap-susceptibility`
   - Cost: ~1.5 days

**Dependency:** Only need UserProgress to properly populate `missed_syntactic_trap_key`

---

### 🟡 Phase 2.5 - Tier 2 (Week 2)

**Schema Optimization:**

1. **Create StudentTrapSusceptibility Table**
   - Nightly aggregation job
   - Cost: ~1 day
   - Benefit: Dashboard queries drop from 2s to 50ms

2. **Endpoints: question-type-performance, trap-details**
   - Join Question.stem_type_key + accuracy
   - Join QuestionOption.distractor_type_key + explanation
   - Cost: ~1.5 days

3. **Trap-Focused Recommendations**
   - POST /api/study/recommendations/trap-focused
   - Filter Question pool by trap_type
   - Cost: ~1 day

---

### 🔴 Phase 2.5 - Tier 3 (Integration, Week 2-3)

**Cross-Phase Integration:**

1. **Integrate with Phase 2 (Spaced Repetition)**
   - When surfacing due questions, prioritize those with student's susceptible traps
   - Cost: ~1 day

2. **Integrate with Phase 3 (Analytics)**
   - Add trap trends to daily/weekly stats
   - Cost: ~0.5 days

---

## Migration Strategy

### Zero Data Loss

Since UserProgress already exists with historical data:

1. **Backfill opportunity:** 
   - For each historical UserProgress record
   - Join question_id → Question.latest_annotation → syntactic_trap_key
   - Join selected_option_label → QuestionOption.distractor_type_key
   - Update UserProgress.missed_syntactic_trap_key if NULL
   - One-time migration, ~30 min to run on 100k rows

2. **Prospective:**
   - All new answers populate `missed_syntactic_trap_key` via frontend
   - Nightly aggregation builds StudentTrapSusceptibility

---

## Code Locations for Integration Points

### Frontend Changes Needed

**File:** `APP/STUDENT_APP_REDUX/src/hooks/useGrammarSession.ts`

**Current (line ~210-230):**
```typescript
const result = await api.submitAnswer({
  question_id: (state.question as any).id,
  selected_option_label: optionId,
  user_token: USER_TOKEN,
  missed_grammar_focus_key: (state.question as any).grammar_focus_key,
  // ❌ missing: missed_syntactic_trap_key
})
```

**Add:**
```typescript
// Extract trap type from selected option
const selectedOption = (state.question as any).options.find(o => o.label === optionId)
const trapType = selectedOption?.distractor_type_key || null

const result = await api.submitAnswer({
  question_id: (state.question as any).id,
  selected_option_label: optionId,
  user_token: USER_TOKEN,
  missed_grammar_focus_key: (state.question as any).grammar_focus_key,
  missed_syntactic_trap_key: trapType,  // ✅ Add this
})
```

### Backend Query Pattern (Existing Endpoint Extension)

**File:** `backend/app/routers/student.py`

**New endpoint around line 1430 (after /study/missed):**

```python
@router.get("/student/trap-susceptibility", response_model=StudentTrapSusceptibilityResponse)
async def get_trap_susceptibility(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """
    Query UserProgress directly:
    - GROUP BY missed_syntactic_trap_key
    - Calculate fall_rate = 1 - (SUM(is_correct) / COUNT(*))
    - Identify top 5 by fall_rate
    - Detect improvement (compare first 5 vs last 5 attempts)
    """
    user = await _resolve_user_by_token(user_token, db)
    
    result = await db.execute(
        select(
            UserProgress.missed_syntactic_trap_key,
            func.count().label("attempts"),
            func.sum(case((UserProgress.is_correct, 1), else_=0)).label("correct"),
        )
        .where(UserProgress.user_id == user.id)
        .where(UserProgress.missed_syntactic_trap_key.isnot(None))
        .group_by(UserProgress.missed_syntactic_trap_key)
        .order_by(func.count().desc())
    )
    
    # Compute fall_rates, identify patterns, detect improvements
    # Return aggregated response
```

---

## Success Metrics (Measurable)

| Metric | Target | How to Verify |
|--------|--------|---------------|
| **Data Capture** | 95%+ of answers include `missed_syntactic_trap_key` | Query UserProgress, count non-NULL trap_keys |
| **Accuracy** | Fall rates match manual review | Sample 100 rows, manually validate |
| **Query Performance** | Trap susceptibility query < 200ms | Bench with `EXPLAIN ANALYZE` |
| **Dashboard UX** | Renders in < 1s | Browser DevTools timing |
| **Improvement Detection** | Identify improving traps correctly | Compare first 5 vs last 5 attempts |
| **Coverage** | 100% of questions have trap classification | Query Questions → annotation_jsonb.syntactic_trap_key |

---

## Open Questions for Implementation

1. **Trap Synonym Handling:**
   - Do `distractor_type_key` (from option) and `syntactic_trap_key` (from annotation) use same identifier space?
   - Need: Reconcile if they're different vocabularies

2. **Backfill Strategy:**
   - Should we backfill all historical UserProgress records with trap data?
   - Or start fresh from today?
   - Recommendation: Backfill (data is there, just needs to be extracted)

3. **Null Handling:**
   - Some questions may not have trap classification
   - How to represent in API? (NULL vs "unknown" string vs omit from results)

4. **Nightly Aggregation Job:**
   - Should run after all student activity peaks (midnight UTC?)
   - Incremental vs full recalculation?
   - Recommendation: Incremental on new/updated UserProgress rows

---

## Conclusion

**Status:** 65% infrastructure ready, 35% needs implementation.

**Starting Point:** Update frontend to extract and send `missed_syntactic_trap_key` (1-2 days).

**Quick Wins:** Endpoints using UserProgress aggregation (2-3 days).

**Optimization:** StudentTrapSusceptibility table + nightly job (1-2 days).

**Total Phase 2.5 Implementation:** ~2 weeks (vs. 3 weeks without existing infrastructure).
