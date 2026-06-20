# Student Tracking Backend PRD

## Executive Summary

The Student Tracking Backend provides comprehensive learner analytics, session management, and adaptive learning support. Current implementation tracks individual question attempts through `UserProgress` table. This PRD expands the system to include:

1. **Diagnostic Session Management** — Group diagnostic attempts into persistent sessions
2. **Spaced Repetition Engine** — SM-2 algorithm for resurface timing of missed questions
3. **Question Type & Distractor Trap Analysis** — Track which traps students fall for and personalize practice
4. **Progress Analytics** — Trend analysis of student performance over time
5. **Adaptive Routing** — Support for module 2 difficulty selection based on module 1 performance
6. **Student Performance Cohort Analysis** — System-wide weak spot identification

---

## Phase 1: Diagnostic Session Management (MVP)

### Goal
Create a persistent storage layer for diagnostic sessions so students can review historical diagnostic results and track improvement over time.

### Current State
- Individual question answers stored in `UserProgress` table
- Diagnostic results calculated client-side only
- No way to retrieve or replay past diagnostics
- Results lost on page refresh or "Try Again"

### Solution Architecture

#### 1.1 Database Schema

```sql
-- New table: diagnostic_sessions
CREATE TABLE diagnostic_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Session metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    total_questions INTEGER NOT NULL,
    correct_count INTEGER NOT NULL,
    accuracy FLOAT NOT NULL,
    
    -- Question tracking
    question_ids UUID[] NOT NULL,  -- Array of question IDs in order asked
    
    -- Context
    diagnostic_type VARCHAR(20),  -- "adaptive", "standard", "focused"
    focus_areas VARCHAR[] DEFAULT ARRAY[]::VARCHAR[],  -- What was being tested
    
    -- Analysis
    is_archived BOOLEAN DEFAULT FALSE,
    notes TEXT,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_accuracy (accuracy)
);

-- Link UserProgress records to diagnostic sessions
ALTER TABLE user_progress ADD COLUMN diagnostic_session_id UUID REFERENCES diagnostic_sessions(id);
ALTER TABLE user_progress ADD INDEX idx_diagnostic_session_id (diagnostic_session_id);
```

#### 1.2 API Endpoints

**POST /api/diagnostic/start**
```json
{
  "diagnostic_type": "adaptive",  // "adaptive" | "standard" | "focused"
  "focus_areas": ["subject_verb_agreement", "verb_tense"]  // optional
}

Response:
{
  "session_id": "uuid-here",
  "user_token": "jwt-token",
  "max_questions": 8,
  "estimated_duration_minutes": 12
}
```

**POST /api/diagnostic/{session_id}/submit**
```json
{
  "question_id": "uuid",
  "selected_option_label": "A",
  "missed_grammar_focus_key": "subject_verb_agreement",
  "timestamp": "2024-06-20T10:30:00Z"
}

Response:
{
  "is_correct": true,
  "progress": {
    "question_number": 3,
    "total_questions": 8,
    "correct_so_far": 2
  }
}
```

**POST /api/diagnostic/{session_id}/complete**
```json
{
  "completed_at": "2024-06-20T10:45:00Z"
}

Response:
{
  "session_id": "uuid",
  "total_questions": 8,
  "correct_count": 6,
  "accuracy": 0.75,
  "duration_seconds": 900,
  "weakest_focus_areas": [
    {"focus_key": "subject_verb_agreement", "miss_count": 2},
    {"focus_key": "verb_tense", "miss_count": 0}
  ]
}
```

**GET /api/diagnostic/history**
```json
Response:
{
  "sessions": [
    {
      "session_id": "uuid",
      "created_at": "2024-06-20T10:00:00Z",
      "completed_at": "2024-06-20T10:45:00Z",
      "accuracy": 0.75,
      "total_questions": 8,
      "correct_count": 6,
      "diagnostic_type": "adaptive",
      "duration_seconds": 900
    }
  ],
  "total_sessions": 5,
  "average_accuracy": 0.72,
  "improvement_trend": 0.08  // -1 to 1, shows if improving
}
```

**GET /api/diagnostic/{session_id}**
```json
Response:
{
  "session_id": "uuid",
  "user_id": 123,
  "created_at": "2024-06-20T10:00:00Z",
  "completed_at": "2024-06-20T10:45:00Z",
  "total_questions": 8,
  "correct_count": 6,
  "accuracy": 0.75,
  "question_results": [
    {
      "question_number": 1,
      "question_id": "uuid",
      "selected_option": "A",
      "is_correct": true,
      "focus_area": "subject_verb_agreement",
      "explanation": "..."
    }
  ],
  "focus_breakdown": {
    "subject_verb_agreement": {"attempted": 2, "correct": 0},
    "verb_tense": {"attempted": 2, "correct": 2}
  }
}
```

**GET /api/diagnostic/{session_id}/export?format=pdf|json**
```
Returns PDF or JSON export of full diagnostic results
```

#### 1.3 Frontend Integration

**Frontend Changes Required:**

1. **DiagnosticTab.tsx** — Update to:
   - Call `POST /api/diagnostic/start` when diagnostic begins
   - Store `session_id` in state
   - Pass `session_id` to each answer submission
   - Call `POST /api/diagnostic/{session_id}/complete` when done
   - Show session archive button

2. **New Component: DiagnosticHistory.tsx**
   - List all past diagnostics with accuracy, date, duration
   - Click to view full results
   - Show improvement trend chart
   - Export button for each session

3. **New Component: DiagnosticDetail.tsx**
   - Full breakdown of specific diagnostic
   - Question-by-question results
   - Focus area breakdown
   - Compare with previous diagnostic

### Phase 1 Deliverables
- [ ] `DiagnosticSession` table + indices
- [ ] 5 API endpoints (start, submit, complete, history, detail)
- [ ] Export endpoint (PDF generation)
- [ ] Frontend: DiagnosticTab updates
- [ ] Frontend: DiagnosticHistory component
- [ ] Frontend: DiagnosticDetail component
- [ ] Tests: Backend endpoint tests (pytest)
- [ ] Tests: Frontend integration tests

### Phase 1 Success Metrics
- Students can retrieve any past diagnostic
- Diagnostic history shows improvement trend
- Session data persists across page refreshes
- Export PDF works for record-keeping
- Average query latency < 200ms for session retrieval

---

## Phase 2: Spaced Repetition Engine

### Goal
Automatically resurface missed questions at optimal times using SM-2 algorithm for long-term retention.

### How It Works

**SM-2 Algorithm Overview:**
```
Initial easiness (EF) = 2.5
Initial interval = 1 day

After each review:
1. Grade response (0-5 scale)
2. Calculate new EF: EF' = max(1.3, EF + 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
3. If quality >= 3: next_interval = previous_interval * EF'
4. If quality < 3: reset interval to 1, reset repetition count
```

#### 2.1 Database Schema

```sql
CREATE TABLE spaced_repetition_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    question_id UUID NOT NULL REFERENCES questions(id),
    
    -- SM-2 state
    easiness_factor FLOAT DEFAULT 2.5,  -- 1.3 to 5.0
    repetition_count INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    next_review_at TIMESTAMP WITH TIME ZONE,  -- When to resurface
    
    -- Tracking
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    quality_grades INTEGER[] DEFAULT ARRAY[]::INTEGER[],  -- [0-5] history
    
    -- Metadata
    source_session_type VARCHAR(20),  -- "diagnostic", "grammar_practice", "test"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_question FOREIGN KEY (question_id) REFERENCES questions(id),
    CONSTRAINT unique_user_question UNIQUE (user_id, question_id),
    INDEX idx_next_review_at (next_review_at),
    INDEX idx_user_id (user_id),
    INDEX idx_quality_grade (quality_grades)
);
```

#### 2.2 API Endpoints

**POST /api/spaced-repetition/{question_id}/review**
```json
{
  "quality_grade": 4,  // 0-5 (0=fail, 5=perfect)
  "response_time_seconds": 45,
  "session_context": {
    "session_type": "grammar_practice",
    "session_id": "uuid"
  }
}

Response:
{
  "question_id": "uuid",
  "next_review_at": "2024-06-27T10:00:00Z",
  "days_until_next_review": 7,
  "confidence_level": "developing"  // novice | developing | proficient | mastered
}
```

**GET /api/spaced-repetition/due-questions**
```json
Query params:
- domain: "grammar" | "reading"
- limit: 10
- offset: 0

Response:
{
  "due_questions": [
    {
      "question_id": "uuid",
      "days_overdue": 3,
      "confidence_level": "developing",
      "last_reviewed": "2024-06-13T10:00:00Z",
      "next_scheduled": "2024-06-20T10:00:00Z",
      "original_source_session": "diagnostic_session_123"
    }
  ],
  "total_due": 24,
  "user_recommendations": {
    "suggested_session_length": 15,  // mins
    "focus_area": "subject_verb_agreement"
  }
}
```

**GET /api/spaced-repetition/progress**
```json
Response:
{
  "total_questions_tracked": 150,
  "mastered_count": 42,  // confidence "mastered"
  "proficient_count": 68,
  "developing_count": 35,
  "novice_count": 5,
  "due_for_review": 24,
  "average_easiness_factor": 2.3,
  "retention_rate": 0.85
}
```

#### 2.3 Integration Points

1. **After Diagnostic** — Auto-populate `spaced_repetition_state` for all diagnostic questions
2. **After Any Question** — Update `spaced_repetition_state` with new quality grade
3. **Dashboard** — Show "X questions due for review" widget
4. **Study Recommendations** — Prioritize due questions in recommendations
5. **Adaptive Module 2** — Use retention scores to decide difficulty routing

### Phase 2 Deliverables
- [ ] `SpacedRepetitionState` table + indices
- [ ] SM-2 calculation engine
- [ ] 3 API endpoints (review, due-questions, progress)
- [ ] Auto-populate on diagnostic completion
- [ ] Dashboard widget showing due questions
- [ ] Tests: Algorithm correctness (various quality grades)
- [ ] Tests: Due question ranking

### Phase 2 Success Metrics
- Due questions correctly scheduled by SM-2 algorithm
- Review API updates EF and next review date correctly
- Dashboard shows accurate "due for review" count
- Retention rate > 80% for mastered items
- Queries for due questions return in < 300ms

---

## Phase 2.5: Question Type & Distractor Trap Analysis

### Goal
Track which types of questions and distractor traps students struggle with, enabling personalized learning targeting specific weaknesses.

### Current State
- No tracking of question types or difficulty patterns
- No analysis of distractor trap effectiveness on students
- Can't identify "this student always falls for modifier traps"
- Can't recommend "practice questions with modifier traps" specifically

### Solution Architecture

#### 2.5.1 Data Model

**Question Type Classification:**
```
Grammar:
  - subject_verb_agreement
  - verb_tense_consistency
  - pronoun_antecedent_agreement
  - modifier_placement
  - parallel_structure
  - punctuation
  - sentence_fragments
  - comma_splice
  - run_on_sentence

Reading:
  - evidence_supports_claim
  - evidence_weakens_claim
  - contextual_meaning
  - main_idea
  - inference
  - text_structure
  - cross_text_connections
```

**Distractor Trap Types:**
```
Grammar Traps:
  - subject_number_mismatch (student picks verb that agrees with object instead of subject)
  - tense_consistency (student picks tense that makes sense but violates passage consistency)
  - parallelism (student picks option that sounds natural but breaks parallel structure)
  - modifier_reference (student picks modifier that logically makes sense but attaches to wrong noun)
  - punctuation_convention (student picks what "sounds right" over proper punctuation)

Reading Traps:
  - recency_bias (student picks last-mentioned similar answer)
  - scope_expansion (student picks answer that's true but too broad for question)
  - scope_reduction (student picks answer that's true but too narrow)
  - emotional_appeal (student picks answer that matches their opinion, not text)
  - partially_correct (student picks answer that's half-right, missing nuance)
  - opposite_answer (student picks logically opposite answer)
```

#### 2.5.2 Database Schema

```sql
-- Track question attributes
CREATE TABLE question_attributes (
    id BIGSERIAL PRIMARY KEY,
    question_id UUID NOT NULL REFERENCES questions(id),
    
    -- Question type classification
    question_type VARCHAR(50),  -- subject_verb_agreement, evidence_supports_claim, etc.
    question_subtype VARCHAR(100),  -- More specific classification
    difficulty_level VARCHAR(20),  -- easy, medium, hard
    
    -- Trap information
    primary_trap_type VARCHAR(50),  -- The main distractor mechanism
    secondary_trap_types VARCHAR[] DEFAULT ARRAY[]::VARCHAR[],  -- Other traps present
    trap_intensity VARCHAR(20),  -- subtle, moderate, strong
    
    -- Metadata from question annotation
    bloom_level VARCHAR(20),  -- recall, understand, apply, analyze, evaluate, create
    requires_passage_context BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_question FOREIGN KEY (question_id) REFERENCES questions(id),
    CONSTRAINT unique_question_attrs UNIQUE (question_id),
    INDEX idx_question_type (question_type),
    INDEX idx_trap_type (primary_trap_type)
);

-- Track student responses to understand trap susceptibility
CREATE TABLE student_trap_interactions (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question_id UUID NOT NULL REFERENCES questions(id),
    user_progress_id INTEGER NOT NULL REFERENCES user_progress(id),
    
    -- Answer details
    selected_option_label VARCHAR(1) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    response_time_seconds INTEGER,
    
    -- Trap information
    question_type VARCHAR(50),  -- Denormalized for query speed
    primary_trap_type VARCHAR(50),
    trap_intensity VARCHAR(20),
    selected_trap_type VARCHAR(50),  -- NULL if correct, else the trap they fell for
    
    -- Analysis
    was_trap_triggered BOOLEAN,  -- Did student fall for the trap?
    distractor_plausibility VARCHAR(20),  -- subtle, moderate, strong
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_question FOREIGN KEY (question_id) REFERENCES questions(id),
    INDEX idx_user_trap_type (user_id, primary_trap_type),
    INDEX idx_user_question_type (user_id, question_type),
    INDEX idx_was_trap_triggered (user_id, was_trap_triggered)
);

-- Student trap susceptibility profile
CREATE TABLE student_trap_susceptibility (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Aggregate trap data
    trap_types_encountered JSONB,  -- {trap_type: count}
    trap_fall_rate JSONB,  -- {trap_type: fall_rate (0.0-1.0)}
    most_susceptible_traps VARCHAR[] DEFAULT ARRAY[]::VARCHAR[],  -- Top 5
    
    -- Question type performance
    question_type_performance JSONB,  -- {question_type: {attempted, correct, accuracy}}
    question_type_struggle_ranking VARCHAR[],  -- Ranked by worst performance
    
    -- Patterns
    trap_improvement_trend JSONB,  -- {trap_type: improvement_rate}
    overcoming_traps VARCHAR[],  -- Traps they're getting better at
    persistent_traps VARCHAR[],  -- Traps still struggling with
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT unique_user_susceptibility UNIQUE (user_id),
    INDEX idx_user_id (user_id)
);

-- Recommendations based on trap susceptibility
CREATE TABLE trap_based_recommendations (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- What to practice
    recommended_trap_type VARCHAR(50),
    recommended_question_type VARCHAR(50),
    reason VARCHAR(255),  -- "You fall for this 68% of the time"
    urgency VARCHAR(20),  -- critical, high, medium, low
    
    -- When to practice
    recommended_after_date DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,  -- When student clicked "Practice this"
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_urgency (user_id, urgency),
    INDEX idx_created_at (created_at)
);
```

#### 2.5.3 API Endpoints

**GET /api/student/trap-susceptibility**
```json
Response:
{
  "user_id": 123,
  "total_questions_attempted": 342,
  "trap_encounters": {
    "subject_number_mismatch": 18,
    "tense_consistency": 15,
    "parallelism": 22,
    "modifier_reference": 8,
    "punctuation_convention": 12
  },
  "trap_fall_rates": {
    "subject_number_mismatch": 0.72,  // Falls for this 72% of attempts
    "tense_consistency": 0.47,
    "parallelism": 0.68,
    "modifier_reference": 0.38,
    "punctuation_convention": 0.92  // CRITICAL - nearly always falls for this
  },
  "most_susceptible_traps": [
    {
      "trap_type": "punctuation_convention",
      "fall_rate": 0.92,
      "occurrences": 12,
      "severity": "critical"  // critical | high | moderate | low
    },
    {
      "trap_type": "subject_number_mismatch",
      "fall_rate": 0.72,
      "occurrences": 18,
      "severity": "high"
    }
  ],
  "trap_improvement": {
    "tense_consistency": {
      "first_10_attempts_accuracy": 0.3,
      "last_10_attempts_accuracy": 0.6,
      "improvement_rate": 0.30  // 30% improvement
    }
  },
  "overcoming_traps": ["tense_consistency"],
  "persistent_traps": ["punctuation_convention", "parallelism"]
}
```

**GET /api/student/question-type-performance**
```json
Response:
{
  "by_question_type": [
    {
      "question_type": "subject_verb_agreement",
      "attempted": 45,
      "correct": 32,
      "accuracy": 0.71,
      "trend": "improving",  // improving | stable | declining
      "primary_trap": "subject_number_mismatch",
      "common_mistakes": [
        {"mistake": "picks verb that agrees with object", "count": 8},
        {"mistake": "picks singular when subject is plural", "count": 5}
      ]
    },
    {
      "question_type": "punctuation_comma",
      "attempted": 28,
      "correct": 3,
      "accuracy": 0.11,
      "trend": "declining",
      "primary_trap": "punctuation_convention",
      "needs_urgent_practice": true
    }
  ],
  "easiest_question_types": ["verb_tense_consistency"],
  "hardest_question_types": ["punctuation_comma", "modifier_placement"]
}
```

**POST /api/study/recommendations/trap-focused**
```json
Response:
{
  "recommended_practice_sets": [
    {
      "id": "uuid",
      "focus_trap": "punctuation_convention",
      "focus_question_type": "punctuation_comma",
      "rationale": "You're falling for this 92% of the time. This is your biggest opportunity for improvement.",
      "estimated_practice_questions": 20,
      "estimated_duration_minutes": 25,
      "urgency": "critical",
      "expected_improvement": "If you master this trap, your accuracy could improve by ~15%"
    },
    {
      "focus_trap": "subject_number_mismatch",
      "focus_question_type": "subject_verb_agreement",
      "rationale": "You're improving here! Keep practicing to push from 72% to mastery (95%+).",
      "urgency": "high",
      "expected_improvement": "~5% accuracy boost"
    }
  ]
}
```

**GET /api/student/trap-details/{trap_type}?question_type=subject_verb_agreement**
```json
Response:
{
  "trap_type": "subject_number_mismatch",
  "question_type": "subject_verb_agreement",
  "definition": "Student picks verb form that agrees with nearest noun instead of grammatical subject",
  "your_stats": {
    "times_encountered": 18,
    "times_fell_for_it": 13,
    "fall_rate": 0.72,
    "first_attempt_correctness": 0.33,
    "recent_accuracy": 0.60,  // Last 5 attempts
    "improvement": "improving"
  },
  "example_mistakes": [
    {
      "question_text": "The CEO, along with the board members, [blank] to the decision.",
      "correct_answer": "agrees",
      "student_chose": "agree",
      "explanation": "The subject is 'CEO' (singular). 'Along with' is a prepositional phrase. Student picked 'agree' because they focused on 'board members' (the nearest noun)."
    }
  ],
  "learning_resources": [
    {
      "type": "explanation",
      "title": "Subject-Verb Agreement: Prepositional Phrases",
      "url": "/resources/grammar/subject-verb-phrases"
    }
  ]
}
```

#### 2.5.4 Frontend Components

**New: StudentTrapSusceptibilityDashboard.tsx**
- Shows "Your Biggest Traps" pie chart
- Critical/High/Medium/Low severity indicators
- Click to see detailed breakdown per trap
- "Practice This Trap" button for each

**New: TrapDetailView.tsx**
- Definition of the trap
- Why it's effective
- Examples of questions with this trap
- Student's historical performance on this trap
- Recommended practice set with this trap

**Update: RecommendationsPage.tsx**
- Add "Trap-Focused Practice" section
- Show critical traps needing immediate attention
- Show traps they're successfully overcoming

**Update: QuestionReviewModal.tsx**
- After answering, show:
  - "You fell for a [trap_type]"
  - Why this is a trap
  - How to avoid it next time
  - How often you fall for this specific trap

#### 2.5.5 Data Population Strategy

**Automatic Population:**
1. During ingestion, QA team marks each question with:
   - `primary_trap_type`
   - `secondary_trap_types`
   - `trap_intensity`
   - `question_type`

2. When student answers, system:
   - Records `was_trap_triggered` (true if wrong AND question has trap AND they picked trap answer)
   - Identifies which trap they fell for (map selected option to trap type)
   - Updates `StudentTrapSusceptibility` nightly

3. Spaced repetition surfaces questions with traps they struggle with

### Phase 2.5 Deliverables
- [ ] `QuestionAttributes` table with trap classification
- [ ] `StudentTrapInteractions` table for granular tracking
- [ ] `StudentTrapSusceptibility` table for aggregated profiles
- [ ] `TrapBasedRecommendations` table
- [ ] 3 API endpoints (susceptibility, question-type-perf, trap-details)
- [ ] StudentTrapSusceptibilityDashboard component
- [ ] TrapDetailView component
- [ ] QuestionReviewModal updates
- [ ] Question attribute ingestion process
- [ ] Tests: Trap classification correctness
- [ ] Tests: Fall rate calculation accuracy

### Phase 2.5 Success Metrics
- ✅ 95%+ accuracy in trap identification
- ✅ Fall rate calculations match manual review
- ✅ Trap-focused practice improves accuracy on that trap by >= 15%
- ✅ Students see personal trap profile within 3 clicks
- ✅ API queries return in < 400ms

---

## Phase 3: Progress Analytics & Trending

### Goal
Show student improvement over time with breakdowns by domain, focus area, and question type.

#### 3.1 Database Schema

```sql
-- Aggregated daily snapshot of student progress
CREATE TABLE student_daily_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    
    -- Totals
    total_attempts INTEGER,
    correct_count INTEGER,
    accuracy FLOAT,
    
    -- By domain
    grammar_attempts INTEGER,
    grammar_correct INTEGER,
    reading_attempts INTEGER,
    reading_correct INTEGER,
    
    -- By focus area (top 3 for this user)
    focus_area_stats JSONB,  -- {focus_key: {attempts, correct, accuracy}}
    
    -- Engagement
    questions_mastered_count INTEGER,  -- New mastered items today
    new_due_items_count INTEGER,
    
    -- Time tracking
    total_time_seconds INTEGER,
    average_time_per_question FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT unique_user_date UNIQUE (user_id, date),
    INDEX idx_user_id_date (user_id, date)
);

-- Weekly rollup
CREATE TABLE student_weekly_stats (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    week_starting_date DATE NOT NULL,
    
    total_attempts INTEGER,
    correct_count INTEGER,
    accuracy FLOAT,
    improvement_vs_previous_week FLOAT,  -- -1 to 1
    
    questions_mastered_count INTEGER,
    study_sessions_count INTEGER,
    average_session_length_minutes FLOAT,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT unique_user_week UNIQUE (user_id, week_starting_date)
);
```

#### 3.2 API Endpoints

**GET /api/progress/trend?period=week|month|year**
```json
Response:
{
  "period": "month",
  "start_date": "2024-05-20",
  "end_date": "2024-06-20",
  "datapoints": [
    {
      "date": "2024-05-20",
      "accuracy": 0.65,
      "total_attempts": 12,
      "correct_count": 8,
      "streak_days": 0
    }
  ],
  "summary": {
    "starting_accuracy": 0.65,
    "ending_accuracy": 0.75,
    "improvement_percentage": 10.0,
    "total_questions_answered": 320,
    "study_days": 22,
    "longest_streak": 7
  }
}
```

**GET /api/progress/by-focus-area?period=month**
```json
Response:
{
  "focus_areas": [
    {
      "focus_key": "subject_verb_agreement",
      "domain": "grammar",
      "attempts": 45,
      "correct": 38,
      "accuracy": 0.844,
      "improvement_vs_month_ago": 0.12,
      "status": "improving"  // improving | stable | declining | mastered
    }
  ]
}
```

**GET /api/progress/comparison?compare_user_id=123**
```json
Response:
{
  "current_user": {
    "accuracy": 0.75,
    "percentile": 72,
    "total_attempts": 320
  },
  "comparison_user": {
    "accuracy": 0.82,
    "percentile": 88
  },
  "insights": {
    "areas_behind": ["punctuation_comma", "modifier_placement"],
    "areas_ahead": ["verb_tense_consistency"],
    "effort_gap": 0.2  // 20% fewer attempts than comparison
  }
}
```

#### 3.3 Frontend Components

1. **ProgressDashboard.tsx** — Main analytics view
   - Line chart of accuracy over time
   - Breakdown by domain (bar chart)
   - Streak counter
   - Weekly summary cards

2. **FocusAreaTrend.tsx** — Deep dive per focus area
   - Accuracy trend for selected focus
   - Difficulty breakdown (questions attempted by difficulty)
   - Status indicator (improving/stable/declining)

3. **ComparisonView.tsx** — Optional peer comparison
   - Side-by-side accuracy
   - Percentile ranking
   - Areas to focus on

### Phase 3 Deliverables
- [ ] Daily/weekly aggregation job (runs nightly)
- [ ] 3 API endpoints for trending data
- [ ] ProgressDashboard component
- [ ] FocusAreaTrend component
- [ ] ComparisonView component (optional)
- [ ] Tests: Aggregation correctness

### Phase 3 Success Metrics
- Trend data aggregated nightly with < 2min job duration
- Trend queries return in < 500ms
- Chart rendering smooth with 30+ datapoints
- Trend accurately reflects actual user performance

---

## Phase 4: Adaptive Module 2 Routing

### Goal
Route students to module 2 higher/lower difficulty based on module 1 performance.

#### 4.1 Routing Logic

```python
def route_module_2_difficulty(module_1_accuracy: float, module_1_duration_seconds: int) -> str:
    """
    Route to module 2 difficulty based on module 1 performance.
    
    Accuracy cutoff: >= 0.70 = higher, < 0.70 = lower
    Time bonus: If completed significantly faster than median, boost one level
    """
    
    if module_1_accuracy >= 0.70:
        # Check if speed suggests higher capability
        if module_1_duration_seconds < 600:  # Under 10 min for 27 questions
            return "higher"  # Even more challenging
        return "higher"
    else:
        return "lower"  # Remedial/scaffolded
```

#### 4.2 Database Schema

```sql
CREATE TABLE test_session_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    module_1_results JSONB NOT NULL,  -- accuracy, duration, focus_breakdown
    module_2_difficulty VARCHAR(20),  -- "higher" | "lower"
    module_2_results JSONB,  -- null until completed
    
    estimated_score INTEGER,  -- 200-800 scale (after module 2)
    actual_score INTEGER,  -- If this was a real SAT
    
    test_mode VARCHAR(20),  -- "practice" | "official"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id_created_at (user_id, created_at)
);
```

#### 4.3 API Endpoints

**POST /api/test-session/module-1-complete**
```json
{
  "module_1_accuracy": 0.74,
  "module_1_duration_seconds": 1200,
  "focus_breakdown": {
    "subject_verb_agreement": {"attempts": 3, "correct": 2}
  }
}

Response:
{
  "test_session_id": "uuid",
  "module_2_difficulty": "higher",
  "routing_rationale": "Accuracy >= 0.70"
}
```

**GET /api/test-session/{test_session_id}/module-2-blueprint**
```json
Returns questions for module 2 at selected difficulty
```

### Phase 4 Deliverables
- [ ] Routing algorithm implementation
- [ ] `TestSessionResults` table
- [ ] 2 API endpoints
- [ ] Frontend integration in test flow
- [ ] Tests: Routing correctness for various scenarios

---

## Phase 5: Cohort Analytics (Admin Dashboard)

### Goal
Show system-wide patterns to identify which questions/focus areas are causing problems.

#### 5.1 API Endpoints

**GET /api/admin/analytics/weak-spots**
```json
Response:
{
  "question_wise_misses": [
    {
      "question_id": "uuid",
      "focus_key": "subject_verb_agreement",
      "total_attempts": 145,
      "miss_count": 67,
      "miss_rate": 0.46,
      "rank": 1  // Most commonly missed
    }
  ],
  "focus_area_wide_misses": [
    {
      "focus_key": "punctuation_comma",
      "total_students_attempted": 89,
      "average_miss_rate": 0.42,
      "trend": "increasing"  // vs last month
    }
  ]
}
```

**GET /api/admin/analytics/student-cohort-summary**
```json
Response:
{
  "total_students": 342,
  "active_this_week": 128,
  "average_accuracy": 0.71,
  "accuracy_distribution": {
    "0-0.5": 12,
    "0.5-0.6": 45,
    "0.6-0.7": 98,
    "0.7-0.8": 125,
    "0.8-0.9": 56,
    "0.9-1.0": 6
  },
  "domain_performance": {
    "grammar": {"accuracy": 0.73, "attempts": 5420},
    "reading": {"accuracy": 0.69, "attempts": 4890}
  }
}
```

### Phase 5 Deliverables
- [ ] 2 admin analytics endpoints
- [ ] Admin UI components for cohort view
- [ ] Tests: Analytics calculation correctness

---

## Implementation Timeline

| Phase | Duration | Start | End | Status |
|-------|----------|-------|-----|--------|
| Phase 1: Diagnostic Sessions | 2 weeks | Jun 24 | Jul 8 | Not Started |
| Phase 2: Spaced Repetition | 2.5 weeks | Jul 9 | Jul 26 | Not Started |
| **Phase 2.5: Trap Analysis** | **2 weeks** | **Jul 27** | **Aug 10** | **Not Started** |
| Phase 3: Progress Analytics | 2 weeks | Aug 11 | Aug 25 | Not Started |
| Phase 4: Adaptive Module 2 | 1.5 weeks | Aug 26 | Sep 9 | Not Started |
| Phase 5: Cohort Analytics | 1 week | Sep 10 | Sep 17 | Not Started |
| **Total** | **~11 weeks** | | | |

---

## Success Criteria

### Overall Metrics
- [ ] 95%+ session retrieval accuracy
- [ ] All spaced repetition scheduling within SM-2 spec
- [ ] Progress trend data aggregated nightly
- [ ] No API endpoint exceeds 500ms latency
- [ ] 99%+ data consistency across sessions

### Student Experience
- [ ] Students see diagnostic history within 2 clicks
- [ ] Due questions surfaced in study dashboard
- [ ] Progress chart shows clear improvement/decline trend
- [ ] Module 2 routing matches intended difficulty

### System Health
- [ ] Database indices on critical queries
- [ ] Nightly aggregation completes < 5 minutes
- [ ] No performance degradation with 10k+ active users
- [ ] Query plans optimized (no full table scans on production data)

---

## Cross-Phase Integrations

### Phase 2.5 Integrations with Other Phases

**Phase 2 (Spaced Repetition) + Phase 2.5 (Trap Analysis):**
- Spaced repetition surfaces questions with traps student struggles with
- SM-2 EF adjusted based on whether student is falling for same trap repeatedly
- "Practice this trap" button creates targeted spaced rep queue

**Phase 3 (Analytics) + Phase 2.5:**
- Progress analytics broken down by trap type
- "Trap mastery trend" chart showing improvement on specific traps
- Cohort analytics: "Most common traps system-wide"

**Phase 4 (Adaptive Module 2) + Phase 2.5:**
- Module 2 difficulty selection considers trap susceptibility
- If student struggles with traps despite good accuracy, route to lower difficulty
- Module 2 blueprint can be customized to include/avoid specific traps

**Phase 5 (Cohort Analytics) + Phase 2.5:**
- Identify traps that cause the most failures system-wide
- Question quality review: "This trap is catching 85% of students, might be too subtle"
- Curriculum recommendations: "This trap type isn't tested enough, generate more"

---

## Related Features (Future)

### From future_features.md

1. **Full Test Simulation** (Phase 6)
   - Two-module adaptive test with live routing
   - Score estimation engine (200-800 SAT scale)
   - Timed practice mode
   - Uses trap analysis for adaptive difficulty

2. **Passage-Based Questions Support** (Phase 7)
   - Student UI for passages + questions
   - Highlight/annotation tools
   - Timed reading section
   - Trap tracking for passage-based questions

3. **Progress Over Time Charts** (Phase 3 dependency)
   - Week/month/year views
   - Domain breakdown
   - Improvement rate tracking
   - **Trap improvement trends** (added by Phase 2.5)

4. **Generation Pipeline Enhancements** (Independent)
   - Adaptive second module generation by difficulty
   - Batch scheduling based on student distribution
   - Multi-model validation
   - **Trap-aware question generation** (uses trap data to create targeted practice sets)

### Trap Analysis Enables
- **Curriculum Personalization** — "This student needs modifier_placement practice, not tense_consistency"
- **Question Recommendation Engine** — "Here are 10 questions with subject_number_mismatch traps you struggle with"
- **Teaching Content** — Link to grammar rules that directly address the trap they fell for
- **Automated Feedback** — "You picked the distractor that agrees the object. Remember to identify the grammatical subject."
- **Quality Assurance** — Identify overly obvious or unfair traps in question bank

---

## Database Migration Plan

All migrations use Alembic. Execution order:

```
001_add_diagnostic_sessions.py
002_add_spaced_repetition_state.py
003_add_student_daily_stats.py
004_add_test_session_results.py
005_add_diagnostic_session_id_to_user_progress.py
006_create_indexes.py
```

Rollback plan: Each migration is reversible. Rollback removes tables/columns in reverse order.

---

## Appendix: Data Privacy & Compliance

### GDPR/Privacy Considerations
- Diagnostic session data is personal data — students can request deletion
- Spaced repetition state is derived from learning activity — include in export
- Daily/weekly stats are aggregated — can be anonymized per regulations

### Data Retention Policy
- Diagnostic sessions: Keep for 2 years (student benefit) then archive
- Spaced repetition state: Keep indefinitely (supports learning)
- Student daily stats: Aggregate after 1 year to weekly rollups
- Test session results: Keep indefinitely (learning record)

### Audit Trail
- All diagnostic session state changes logged
- API access to student data logged
- Admin analytics queries logged

---

## Glossary

| Term | Definition |
|------|-----------|
| **SM-2** | Spaced Repetition algorithm (SuperMemo 2) |
| **EF** | Easiness Factor — difficulty multiplier (1.3–5.0) |
| **Quality Grade** | 0–5 self-assessment (0=fail, 5=perfect) |
| **Mastered** | EF ≥ 3.5 and 100% accuracy in last 3 reviews |
| **Due for Review** | next_review_at <= today |
| **Module 1** | 27-question standard SAT verbal section |
| **Module 2** | Adaptive second module (higher/lower difficulty) |
| **Cohort** | All students in the system (for admin analytics) |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| PM | [Your Name] | 2024-06-20 | Pending |
| Tech Lead | [Engineer] | Pending | Pending |
| Product | [Product Owner] | Pending | Pending |
