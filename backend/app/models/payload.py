"""HTTP request/response models."""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Any, Dict, Literal
from datetime import datetime
from uuid import UUID


class StudentQuestionResponse(BaseModel):
    """Student-facing question payload — answer key excluded."""
    id: str
    content_origin: str
    current_question_text: str
    current_passage_text: Optional[str] = None
    passage_tokens: Optional[List[dict]] = None
    practice_status: str
    source_release_year: Optional[int] = None
    source_test_name: Optional[str] = None
    grammar_role_key: Optional[str] = None
    grammar_focus_key: Optional[str] = None
    reading_skill_family_key: Optional[str] = None
    reading_focus_key: Optional[str] = None
    difficulty_overall: Optional[str] = None
    stimulus_mode_key: Optional[str] = None
    source_exam_code: Optional[str] = None
    source_subject_code: Optional[str] = None
    source_section_code: Optional[str] = None
    source_module_code: Optional[str] = None
    options: List[dict] = Field(default_factory=list)
    source_question_number: Optional[int] = None
    question_family_key: Optional[str] = None
    syntactic_trap_key: Optional[str] = None
    reasoning_trap_key: Optional[str] = None
    explanation_short: Optional[str] = None
    solver_pattern_key: Optional[str] = None

    model_config = {"from_attributes": True}


class InventoryMetadata(BaseModel):
    """Active-question inventory summary returned with every /api/questions response."""
    matching_target_total: int
    matching_unseen: int
    served: int
    includes_generated: bool
    below_threshold: bool
    threshold: int


class StudentQuestionsListResponse(BaseModel):
    items: List[StudentQuestionResponse]
    inventory: InventoryMetadata


class QuestionRecallResponse(BaseModel):
    """Admin-facing recall payload — includes answer key."""
    id: str
    content_origin: str
    current_question_text: str
    current_passage_text: Optional[str] = None
    current_correct_option_label: str
    practice_status: str
    source_release_year: Optional[int] = None
    source_test_name: Optional[str] = None
    grammar_role_key: Optional[str] = None
    grammar_focus_key: Optional[str] = None
    difficulty_overall: Optional[str] = None
    stimulus_mode_key: Optional[str] = None
    source_exam_code: Optional[str] = None
    source_subject_code: Optional[str] = None
    source_section_code: Optional[str] = None
    source_module_code: Optional[str] = None
    source_question_number: Optional[int] = None
    generation_profile: Optional[dict] = None

    model_config = {"from_attributes": True}


class QuestionDetailResponse(BaseModel):
    id: str
    content_origin: str
    current_question_text: str
    current_passage_text: Optional[str] = None
    current_correct_option_label: str
    current_explanation_text: Optional[str] = None
    practice_status: str
    official_overlap_status: str
    is_admin_edited: bool
    source_release_year: Optional[int] = None
    source_test_name: Optional[str] = None
    source_exam_code: Optional[str] = None
    source_subject_code: Optional[str] = None
    source_section_code: Optional[str] = None
    source_module_code: Optional[str] = None
    source_question_number: Optional[int] = None
    latest_annotation: Optional[dict] = None
    generation_profile: Optional[dict] = None
    options: List[dict] = Field(default_factory=list)
    lineage: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserProgressCreate(BaseModel):
    user_token: str
    question_id: str
    selected_option_label: str = Field(pattern=r"^[A-D]$")
    missed_grammar_focus_key: Optional[str] = None
    missed_syntactic_trap_key: Optional[str] = None
    # Phase 8: reading equivalents (client-optional; auto-populated from annotation)
    missed_reading_focus_key: Optional[str] = None
    missed_reading_skill_family_key: Optional[str] = None


class UserStats(BaseModel):
    total_answered: int
    total_correct: int
    accuracy: float
    top_missed_focus_keys: List[str] = Field(default_factory=list)
    top_missed_trap_keys: List[str] = Field(default_factory=list)


class AdminEditRequest(BaseModel):
    question_text: Optional[str] = None
    passage_text: Optional[str] = None
    paired_passage_text: Optional[str] = None
    underlined_text: Optional[str] = None
    correct_option_label: Optional[str] = Field(default=None, pattern=r"^[A-D]$")
    explanation_text: Optional[str] = None
    change_notes: Optional[str] = None


class EvaluationScoreRequest(BaseModel):
    score_overall: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    score_metadata: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    score_explanation: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    score_generation: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    review_notes: Optional[str] = None
    recommended_for_default: Optional[bool] = None


class _GenerationTargetRequest(BaseModel):
    target_grammar_role_key: Optional[str] = None
    target_grammar_focus_key: Optional[str] = None
    target_syntactic_trap_key: str = "none"
    target_reading_skill_family_key: Optional[str] = None
    target_skill_family_key: Optional[str] = None
    target_reading_focus_key: Optional[str] = None
    target_test_construct_key: Optional[str] = None
    target_question_family_key: Optional[str] = None
    question_family_key: Optional[str] = None
    difficulty_overall: str = "medium"
    source_question_ids: Optional[List[str]] = None

    @field_validator(
        "target_grammar_role_key",
        "target_grammar_focus_key",
        "target_reading_skill_family_key",
        "target_skill_family_key",
        "target_reading_focus_key",
        "target_test_construct_key",
        "target_question_family_key",
        "question_family_key",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _require_supported_generation_target(self):
        grammar_has_any = bool(self.target_grammar_role_key or self.target_grammar_focus_key)
        grammar_complete = bool(self.target_grammar_role_key and self.target_grammar_focus_key)

        reading_skill = self.target_reading_skill_family_key or self.target_skill_family_key
        reading_has_any = bool(reading_skill or self.target_reading_focus_key)
        reading_complete = bool(reading_skill and self.target_reading_focus_key)

        if grammar_has_any and not grammar_complete:
            raise ValueError(
                "Grammar generation requires both target_grammar_role_key "
                "and target_grammar_focus_key"
            )
        if reading_has_any and not reading_complete:
            raise ValueError(
                "Reading generation requires target_reading_focus_key plus "
                "target_reading_skill_family_key or target_skill_family_key"
            )
        if not grammar_complete and not reading_complete:
            raise ValueError(
                "Generation requests must include either a complete grammar target "
                "or a complete reading target"
            )
        return self


class GenerationRequest(_GenerationTargetRequest):
    provider_name: Optional[str] = None
    model_name: Optional[str] = None


class GenerationCompareRequest(_GenerationTargetRequest):
    providers: List[str] = Field(default_factory=lambda: ["ollama"])


# --- Phase 1: Generation batch contract --------------------------------------
#
# Stricter than `GenerationRequest`. Enforces the full mandatory-field lists
# from the rules-agent canon:
#
#   * grammar: rules_agent_dsat_grammar_ingestion_generation_v8.md §B.1.1
#   * reading: rules_agent_dsat_reading_v3.md §16.1 (+ §2.2 conditionals)
#
# A request that wouldn't pass the rules-agent's own "validate generation
# request" step (Step 1 of B.2 in the grammar doc) is rejected here with
# 422 before any job is queued.

ReleasePolicy = Literal["admin_review_required", "auto_release_on_accept", "dry_run"]


class GenerationBatchRequest(BaseModel):
    # --- Quantity ---
    requested_count: int = Field(..., ge=1, description="Number of questions to generate in this batch.")

    # --- Workflow ---
    release_policy: ReleasePolicy = "admin_review_required"
    skip_review: bool = False

    # --- Source examples (caller-supplied; auto-selected when empty) ---
    source_question_ids: Optional[List[str]] = None

    # --- Optional provider/model override (operational; stripped from lineage) ---
    provider_name: Optional[str] = None
    model_name: Optional[str] = None

    # --- Common shared spec ---
    difficulty_overall: str = "medium"
    stimulus_mode_key: Optional[str] = None
    stem_type_key: Optional[str] = None

    # --- Grammar target fields (per v8 §B.1.1) ---
    target_grammar_role_key: Optional[str] = None
    target_grammar_focus_key: Optional[str] = None
    target_syntactic_trap_key: str = "none"
    target_frequency_band: Optional[str] = None
    test_format_key: Optional[str] = None

    # Conditional grammar (transition_logic items)
    target_transition_subtype_key: Optional[str] = None
    distractor_transition_subtypes: Optional[List[str]] = None

    # Conditional grammar (choose_best_notes_synthesis items)
    target_synthesis_goal_key: Optional[str] = None
    target_audience_knowledge_key: Optional[str] = None
    target_required_content_key: Optional[str] = None
    distractor_synthesis_failures: Optional[List[str]] = None

    # --- Reading target fields (per v2 §16.1) ---
    target_skill_family_key: Optional[str] = None
    target_reading_skill_family_key: Optional[str] = None  # legacy alias
    target_reading_focus_key: Optional[str] = None
    target_test_construct_key: Optional[str] = None
    target_craft_subconstruct_key: Optional[str] = None
    target_reasoning_trap_key: Optional[str] = None
    target_distractor_pattern: Optional[List[str]] = None
    passage_structure_pattern: Optional[str] = None

    # Conditional reading (per v2 §2.2)
    polarity_context: Optional[str] = None
    target_sentence_function_role: Optional[str] = None
    quantitative_sub_pattern: Optional[str] = None
    passage_architecture_key: Optional[str] = None
    inference_type_note: Optional[str] = None
    two_part_claim: Optional[bool] = None

    # Question family (used to determine when craft_subconstruct is required)
    question_family_key: Optional[str] = None

    @field_validator(
        "target_grammar_role_key", "target_grammar_focus_key",
        "target_frequency_band", "test_format_key",
        "target_skill_family_key", "target_reading_skill_family_key",
        "target_reading_focus_key", "target_test_construct_key",
        "target_craft_subconstruct_key", "target_reasoning_trap_key",
        "passage_structure_pattern", "stimulus_mode_key", "stem_type_key",
        "question_family_key", "target_transition_subtype_key",
        "target_synthesis_goal_key", "target_audience_knowledge_key",
        "target_required_content_key", "polarity_context",
        "target_sentence_function_role", "quantitative_sub_pattern",
        "passage_architecture_key", "inference_type_note",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _enforce_rules_canon(self):
        grammar_has_any = bool(
            self.target_grammar_role_key or self.target_grammar_focus_key
        )
        reading_skill = self.target_reading_skill_family_key or self.target_skill_family_key
        reading_has_any = bool(reading_skill or self.target_reading_focus_key)

        if grammar_has_any and reading_has_any:
            raise ValueError(
                "Batch request mixes grammar and reading target fields; "
                "specify one domain per batch."
            )
        if not grammar_has_any and not reading_has_any:
            raise ValueError(
                "Batch request must specify either a grammar target or a "
                "reading target."
            )

        if grammar_has_any:
            self._enforce_grammar_mandatory()
        else:
            self._enforce_reading_mandatory()

        return self

    # --- Internal: per-domain mandatory enforcement ---

    _GRAMMAR_MANDATORY: tuple = (
        # (attribute, public field name shown in error)
        ("target_grammar_role_key", "target_grammar_role_key"),
        ("target_grammar_focus_key", "target_grammar_focus_key"),
        ("target_frequency_band", "target_frequency_band"),
        ("difficulty_overall", "difficulty_overall"),
        ("test_format_key", "test_format_key"),
        ("stimulus_mode_key", "stimulus_mode_key"),
        ("stem_type_key", "stem_type_key"),
    )

    _READING_MANDATORY: tuple = (
        # target_skill_family_key OR target_reading_skill_family_key handled
        # specially below
        ("target_reading_focus_key", "target_reading_focus_key"),
        ("target_test_construct_key", "target_test_construct_key"),
        ("target_reasoning_trap_key", "target_reasoning_trap_key"),
        ("target_distractor_pattern", "target_distractor_pattern"),
        ("passage_structure_pattern", "passage_structure_pattern"),
        ("stimulus_mode_key", "stimulus_mode_key"),
        ("stem_type_key", "stem_type_key"),
        ("difficulty_overall", "difficulty_overall"),
    )

    def _enforce_grammar_mandatory(self):
        missing = [
            label for attr, label in self._GRAMMAR_MANDATORY
            if not getattr(self, attr)
        ]
        if missing:
            raise ValueError(
                "Grammar batch request is missing required field(s) "
                f"{missing}; see rules_agent_dsat_grammar_ingestion_"
                "generation_v8.md §B.1.1."
            )

        # `very_low` frequency requires explicit justification per v8 §B.1.1.
        # The batch endpoint does not accept it.
        if self.target_frequency_band == "very_low":
            raise ValueError(
                "target_frequency_band='very_low' is not accepted by the "
                "batch endpoint without explicit justification "
                "(see v8 §B.1.1)."
            )

        # Conditional: transition_logic items need transition subtype +
        # distractor list (3 items).
        if self.target_grammar_focus_key == "transition_logic":
            cond_missing = []
            if not self.target_transition_subtype_key:
                cond_missing.append("target_transition_subtype_key")
            if not self.distractor_transition_subtypes or len(self.distractor_transition_subtypes) != 3:
                cond_missing.append("distractor_transition_subtypes (array of 3)")
            if cond_missing:
                raise ValueError(
                    "transition_logic grammar requests require additional "
                    f"field(s): {cond_missing}; see v8 §B.1.1."
                )

        # Conditional: choose_best_notes_synthesis items need synthesis
        # goal/audience/content + distractor failures (3 items).
        if self.target_grammar_focus_key == "choose_best_notes_synthesis" or \
                self.stem_type_key == "choose_best_notes_synthesis":
            cond_missing = []
            if not self.target_synthesis_goal_key:
                cond_missing.append("target_synthesis_goal_key")
            if not self.target_audience_knowledge_key:
                cond_missing.append("target_audience_knowledge_key")
            if not self.target_required_content_key:
                cond_missing.append("target_required_content_key")
            if not self.distractor_synthesis_failures or len(self.distractor_synthesis_failures) != 3:
                cond_missing.append("distractor_synthesis_failures (array of 3)")
            if cond_missing:
                raise ValueError(
                    "choose_best_notes_synthesis grammar requests require "
                    f"additional field(s): {cond_missing}; see v8 §B.1.1."
                )

    def _enforce_reading_mandatory(self):
        # Skill family is required, accepting either alias.
        if not (self.target_skill_family_key or self.target_reading_skill_family_key):
            raise ValueError(
                "Reading batch request requires target_skill_family_key "
                "(or alias target_reading_skill_family_key); see "
                "rules_agent_dsat_reading_v3.md §16.1."
            )

        missing = [
            label for attr, label in self._READING_MANDATORY
            if not getattr(self, attr)
        ]
        # target_distractor_pattern must be a list of exactly 3 items if
        # present
        if self.target_distractor_pattern is not None and len(self.target_distractor_pattern) != 3:
            raise ValueError(
                "target_distractor_pattern must be an array of exactly 3 "
                "items (per v3 §16.1)."
            )

        if missing:
            raise ValueError(
                "Reading batch request is missing required field(s) "
                f"{missing}; see rules_agent_dsat_reading_v3.md §16.1."
            )

        # Conditional fields from v2 §2.2
        skill = self.target_skill_family_key or self.target_reading_skill_family_key
        focus = self.target_reading_focus_key

        if focus == "polarity_fit" and not self.polarity_context:
            raise ValueError(
                "target_reading_focus_key='polarity_fit' requires "
                "polarity_context (per v2 §2.2)."
            )
        if focus == "sentence_function" and not self.target_sentence_function_role:
            raise ValueError(
                "target_reading_focus_key='sentence_function' requires "
                "target_sentence_function_role (per v2 §2.2)."
            )
        if skill == "command_of_evidence_quantitative" and not self.quantitative_sub_pattern:
            raise ValueError(
                "target_skill_family_key='command_of_evidence_quantitative' "
                "requires quantitative_sub_pattern (per v2 §2.2)."
            )
        if self.question_family_key == "craft_and_structure" and not self.target_craft_subconstruct_key:
            raise ValueError(
                "question_family_key='craft_and_structure' requires "
                "target_craft_subconstruct_key (per v2 §2.2)."
            )
        if focus == "evidence_illustrates_claim" and self.two_part_claim is None:
            raise ValueError(
                "target_reading_focus_key='evidence_illustrates_claim' "
                "requires two_part_claim (boolean, per v2 §2.2)."
            )


class GenerationBatchResponse(BaseModel):
    id: str
    status: str
    requested_count: int
    created_at: Optional[datetime] = None
    job_ids: List[str] = Field(default_factory=list)
    idempotent_replay: bool = False

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    question_id: Optional[str] = None
    created_at: Optional[datetime] = None
    validation_errors: Optional[List[Any]] = None
    ocr_meta: Optional[Dict[str, Any]] = None
    llm_meta: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ReannotateRequest(BaseModel):
    provider_name: str = "ollama"
    model_name: str = "deepseek-v4-pro:cloud"


class OCRJobResult(BaseModel):
    job_id: str
    strategy: str
    status: str
    ocr_meta: Optional[dict] = None
    llm_meta: Optional[dict] = None
    pass2_meta: Optional[List[dict]] = None
    questions_extracted: int = 0
    questions_created: int = 0
    validation_errors: Optional[List[Any]] = None


class OCRBenchmarkResponse(BaseModel):
    comparison_group_id: str
    results: List[OCRJobResult]
    ready: bool
    has_images: bool = True


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str = "student"
    user_token: UUID
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Student auth payloads -------------------------------------------------


class StudentSignup(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(min_length=8, max_length=128)


class StudentLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class StudentMeResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime


# --- Phase 8: Self-study agent request layer ---------------------------------


class WeaknessTarget(BaseModel):
    """One identified weak target dimension from the student's progress history."""
    domain: str
    focus_key: str
    skill_family_key: Optional[str] = None
    grammar_role_key: Optional[str] = None
    difficulty: str
    weakness_score: float
    miss_count: int
    attempt_count: int
    miss_rate: float
    days_since_last_attempt: float
    inventory_unseen: int
    inventory_below_threshold: bool


class MissedQuestionItem(BaseModel):
    question_id: str
    question_text: str
    domain: Optional[str] = None
    focus_key: Optional[str] = None
    difficulty: Optional[str] = None
    user_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    miss_count: int
    last_missed_at: Optional[datetime] = None


class MissedQuestionsResponse(BaseModel):
    user_id: int
    items: List[MissedQuestionItem]
    total: int


class StudyRecommendationsRequest(BaseModel):
    user_token: str


class StudyRecommendationsResponse(BaseModel):
    user_id: int
    top_targets: List[WeaknessTarget]
    threshold: int


class StudyGenerationRequest(BaseModel):
    user_token: str


class StudyGenerationResponse(BaseModel):
    user_id: int
    questions: List[StudentQuestionResponse]
    inventory: InventoryMetadata
    new_batch_ids: List[str] = Field(default_factory=list)
    targets_analyzed: int
    targets_with_new_batch: int
    skip_reasons: Dict[str, str] = Field(default_factory=dict)


class StudyBatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    requested_count: int
    created_count: int
    accepted_count: int
    rejected_count: int
    failed_count: int
    needs_review_count: int
    release_policy: str
    requested_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Phase 9: Generation Quality Analytics payload models
# ---------------------------------------------------------------------------

class GeneratorModelStats(BaseModel):
    provider_name: str
    model_name: str
    generated_count: int
    approved_count: int
    rejected_count: int
    acceptance_rate: float


class ReviewerModelStats(BaseModel):
    provider_name: str
    model_name: str
    review_count: int
    avg_realism: Optional[float]
    avg_sat_fidelity: Optional[float]
    avg_difficulty_match: Optional[float]
    avg_distractor_quality: Optional[float]
    avg_taxonomy_match: Optional[float]
    override_rate: Optional[float]
    total_overrides: int
    correct_count: int


class BatchAggregates(BaseModel):
    total_requested: int
    total_created: int
    total_accepted: int
    total_rejected: int
    total_failed: int
    batch_count: int
    avg_review_latency_ms: Optional[float]


class TokenUsageByProvider(BaseModel):
    provider_name: str
    review_count: int
    total_input_tokens: int
    total_output_tokens: int


class GenerationTrendPoint(BaseModel):
    period: str
    generated: int
    approved: int
    rejected: int
    acceptance_rate: float


class RejectionReasonCount(BaseModel):
    reason: Optional[str]
    count: int


class GenerationAnalyticsResponse(BaseModel):
    days: int
    generated_count: int
    reviewed_count: int
    approved_count: int
    rejected_count: int
    failed_count: int
    acceptance_rate: float
    copy_risk_failures: int
    avg_reviewer_disagreement: Optional[float]
    by_generator_model: List[GeneratorModelStats]
    rejection_reasons: List[RejectionReasonCount]


class ReviewAnalyticsResponse(BaseModel):
    days: int
    by_reviewer_model: List[ReviewerModelStats]
    token_usage: List[TokenUsageByProvider]


class BatchAnalyticsResponse(BaseModel):
    days: int
    aggregates: BatchAggregates
    token_usage: List[TokenUsageByProvider]


class TrendAnalyticsResponse(BaseModel):
    days: int
    granularity: str
    points: List[GenerationTrendPoint]


# ── Diagnostic Session Models ────────────────────────────────────────────────

class DiagnosticSessionStartRequest(BaseModel):
    user_token: str
    diagnostic_type: Optional[str] = "standard"
    focus_areas: Optional[List[str]] = None


class DiagnosticSessionStartResponse(BaseModel):
    session_id: str
    max_questions: int = 8
    estimated_duration_minutes: int = 12


class DiagnosticAnswerRequest(BaseModel):
    user_token: str
    question_id: str
    selected_option_label: str = Field(pattern=r"^[A-D]$")
    missed_grammar_focus_key: Optional[str] = None
    missed_syntactic_trap_key: Optional[str] = None
    missed_reading_focus_key: Optional[str] = None
    missed_reading_skill_family_key: Optional[str] = None


class DiagnosticAnswerResponse(BaseModel):
    is_correct: bool
    progress_id: int
    question_number: int
    total_questions: int
    correct_so_far: int


class DiagnosticSessionResult(BaseModel):
    session_id: str
    total_questions: int
    correct_count: int
    accuracy: float
    duration_seconds: Optional[int] = None
    weakest_focus_areas: List[Dict[str, Any]] = Field(default_factory=list)


class DiagnosticHistoryItem(BaseModel):
    session_id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    accuracy: Optional[float] = None
    total_questions: int
    correct_count: int
    diagnostic_type: Optional[str] = None
    duration_seconds: Optional[int] = None


class DiagnosticHistoryResponse(BaseModel):
    sessions: List[DiagnosticHistoryItem]
    total_sessions: int
    average_accuracy: Optional[float] = None
    improvement_trend: Optional[float] = None  # positive = improving


class DiagnosticQuestionResult(BaseModel):
    question_number: int
    question_id: str
    selected_option: str
    is_correct: bool
    focus_area: Optional[str] = None


class DiagnosticSessionDetailResponse(BaseModel):
    session_id: str
    user_id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_questions: int
    correct_count: int
    accuracy: Optional[float] = None
    question_results: List[DiagnosticQuestionResult]
    focus_breakdown: Dict[str, Any] = Field(default_factory=dict)


# ── Spaced Repetition Models ─────────────────────────────────────────────────

class SRReviewRequest(BaseModel):
    user_token: str
    quality: int = Field(ge=0, le=5, description="0=blackout, 5=perfect recall")


class SRReviewResponse(BaseModel):
    question_id: str
    next_review_at: datetime
    interval_days: float
    easiness_factor: float
    repetition_count: int
    confidence_level: str  # "novice" | "developing" | "proficient" | "mastered"


class SRDueQuestion(BaseModel):
    question_id: str
    days_overdue: float
    confidence_level: str
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    focus_area: Optional[str] = None
    domain: Optional[str] = None


class SRDueQuestionsResponse(BaseModel):
    due_questions: List[SRDueQuestion]
    total_due: int
    suggested_session_length_minutes: int


class SRProgressResponse(BaseModel):
    total_tracked: int
    mastered_count: int
    proficient_count: int
    developing_count: int
    novice_count: int
    due_for_review: int
    average_easiness_factor: float
    retention_rate: float  # correct_attempts / total_attempts across all SR records

    model_config = {"from_attributes": True}


class TrapMetric(BaseModel):
    trap_type: str
    fall_rate: float          # 0.0–1.0
    occurrences: int
    correct_count: int
    severity: str             # "critical" | "high" | "moderate" | "low"


class TrapImprovement(BaseModel):
    first_accuracy: float
    recent_accuracy: float
    trend: float              # positive = improving, negative = regressing


class TrapSusceptibilityResponse(BaseModel):
    user_id: int
    total_questions_attempted: int
    trap_encounters: Dict[str, int]
    trap_fall_rates: Dict[str, float]
    trap_correct_counts: Dict[str, int]
    most_susceptible_traps: List[TrapMetric]
    overcoming_traps: List[TrapMetric]
    persistent_traps: List[TrapMetric]
    trap_improvement: Dict[str, TrapImprovement]
