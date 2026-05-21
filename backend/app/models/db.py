import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, SmallInteger, Float, Boolean, Text,
    ForeignKey, DateTime, Enum, JSON, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base
from app.models.ontology import (
    CONTENT_ORIGINS, JOB_TYPES, JOB_STATUSES, PRACTICE_STATUSES,
    OVERLAP_STATUSES, RELATION_TYPES, ASSET_TYPES, CHANGE_SOURCES,
    DISTRACTOR_TYPE_KEYS,
    REVIEW_STATUSES, REVIEW_RUN_STATUSES, TRIGGERED_BY_VALUES,
    REVIEW_VERDICTS, CONSENSUS_VERDICTS,
)

def _utcnow():
    return datetime.now(timezone.utc)


class QuestionJob(Base):
    __tablename__ = "question_jobs"
    __table_args__ = (
        Index("ix_question_jobs_status", "status"),
        Index("ix_question_jobs_created_at", "created_at"),
        Index("ix_question_jobs_comparison_group_id", "comparison_group_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(Enum(*JOB_TYPES, name="job_type_enum"), nullable=False)
    content_origin = Column(Enum(*CONTENT_ORIGINS, name="content_origin_enum"), nullable=False)
    input_format = Column(String(20), nullable=False)
    status = Column(Enum(*JOB_STATUSES, name="job_status_enum"), nullable=False, default="pending")
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    prompt_version = Column(String(20), nullable=False, default="v3.0")
    rules_version = Column(String(100), nullable=False)
    raw_asset_id = Column(UUID(as_uuid=True), ForeignKey("question_assets.id"), nullable=True)
    pass1_json = Column(JSONB, nullable=True)
    pass2_json = Column(JSONB, nullable=True)
    validation_errors_jsonb = Column(JSONB, nullable=True)
    comparison_group_id = Column(UUID(as_uuid=True), nullable=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    generation_batch_id = Column(UUID(as_uuid=True), ForeignKey("generation_batches.id"), nullable=True)
    generation_request_jsonb = Column(JSONB, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    question = relationship("Question", back_populates="jobs", foreign_keys=[question_id])


class QuestionJobQuestion(Base):
    """Junction table linking a job to every question it produced (not just the first)."""
    __tablename__ = "question_job_questions"
    __table_args__ = (
        Index("ix_qjq_job_id", "job_id"),
        Index("ix_qjq_question_id", "question_id"),
    )

    job_id = Column(UUID(as_uuid=True), ForeignKey("question_jobs.id"), primary_key=True, nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_practice_status", "practice_status"),
        Index("ix_questions_content_origin", "content_origin"),
        Index("ix_questions_latest_annotation_id", "latest_annotation_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_origin = Column(Enum(*CONTENT_ORIGINS, name="content_origin_enum"), nullable=False)
    source_exam_code = Column(String(20), nullable=True)
    source_subject_code = Column(String(10), nullable=True)
    source_section_code = Column(String(10), nullable=True)
    source_module_code = Column(String(10), nullable=True)
    source_question_number = Column(Integer, nullable=True)
    stimulus_mode_key = Column(String(100), nullable=True)
    stem_type_key = Column(String(100), nullable=True)
    current_question_text = Column(Text, nullable=False)
    current_passage_text = Column(Text, nullable=True)
    current_paired_passage_text = Column(Text, nullable=True)
    current_underlined_text = Column(Text, nullable=True)
    current_correct_option_label = Column(String(1), nullable=False)
    current_explanation_text = Column(Text, nullable=True)
    practice_status = Column(Enum(*PRACTICE_STATUSES, name="practice_status_enum"), nullable=False, default="draft")
    official_overlap_status = Column(Enum(*OVERLAP_STATUSES, name="overlap_status_enum"), nullable=False, default="none")
    canonical_official_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    derived_from_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    generation_source_set = Column(JSONB, nullable=True)
    is_admin_edited = Column(Boolean, nullable=False, default=False)
    annotation_stale = Column(Boolean, nullable=False, default=False)
    passage_group_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    metadata_managed_by_llm = Column(Boolean, nullable=False, default=True)
    latest_annotation_id = Column(UUID(as_uuid=True), ForeignKey("question_annotations.id"), nullable=True)
    latest_version_id = Column(UUID(as_uuid=True), ForeignKey("question_versions.id"), nullable=True)
    is_canonical_source = Column(Boolean, nullable=False, default=False)
    rejection_reason = Column(Text, nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by_admin_token = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    jobs = relationship("QuestionJob", back_populates="question", foreign_keys="[QuestionJob.question_id]")
    versions = relationship("QuestionVersion", back_populates="question", order_by="QuestionVersion.version_number", foreign_keys="[QuestionVersion.question_id]")
    annotations = relationship("QuestionAnnotation", back_populates="question", foreign_keys="[QuestionAnnotation.question_id]")
    options = relationship("QuestionOption", back_populates="question", order_by="QuestionOption.option_label", foreign_keys="[QuestionOption.question_id]")
    assets = relationship("QuestionAsset", back_populates="question", foreign_keys="[QuestionAsset.question_id]")
    source_spans = relationship("QuestionSourceSpan", back_populates="question", foreign_keys="[QuestionSourceSpan.question_id]")
    stimulus_assets = relationship("QuestionStimulusAsset", back_populates="question", foreign_keys="[QuestionStimulusAsset.question_id]")
    outgoing_relations = relationship("QuestionRelation", back_populates="from_question", foreign_keys="[QuestionRelation.from_question_id]")
    incoming_relations = relationship("QuestionRelation", back_populates="to_question", foreign_keys="[QuestionRelation.to_question_id]")
    progress_records = relationship("UserProgress", back_populates="question", foreign_keys="[UserProgress.question_id]")


class QuestionVersion(Base):
    __tablename__ = "question_versions"
    __table_args__ = (
        UniqueConstraint("question_id", "version_number", name="uq_question_versions_question_version_number"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    change_source = Column(Enum(*CHANGE_SOURCES, name="change_source_enum"), nullable=False)
    question_text = Column(Text, nullable=False)
    passage_text = Column(Text, nullable=True)
    paired_passage_text = Column(Text, nullable=True)
    underlined_text = Column(Text, nullable=True)
    choices_jsonb = Column(JSONB, nullable=False)
    correct_option_label = Column(String(1), nullable=False)
    explanation_text = Column(Text, nullable=True)
    editor_user_id = Column(String(50), nullable=True)
    change_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="versions", foreign_keys=[question_id])


class QuestionAnnotation(Base):
    __tablename__ = "question_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    question_version_id = Column(UUID(as_uuid=True), ForeignKey("question_versions.id"), nullable=False)
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    prompt_version = Column(String(20), nullable=False)
    rules_version = Column(String(100), nullable=False)
    annotation_jsonb = Column(JSONB, nullable=False, default=dict)
    explanation_jsonb = Column(JSONB, nullable=False, default=dict)
    generation_profile_jsonb = Column(JSONB, nullable=True)
    confidence_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="annotations", foreign_keys=[question_id])


class QuestionOption(Base):
    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_version_id", "option_label", name="uq_question_options_version_label"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    question_version_id = Column(UUID(as_uuid=True), ForeignKey("question_versions.id"), nullable=False)
    option_label = Column(String(1), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    option_role = Column(String(10), nullable=False)
    distractor_type_key = Column(String(100), nullable=True)
    semantic_relation_key = Column(String(100), nullable=True)
    plausibility_source_key = Column(String(100), nullable=True)
    option_error_focus_key = Column(String(100), nullable=True)
    why_plausible = Column(Text, nullable=True)
    why_wrong = Column(Text, nullable=True)
    grammar_fit = Column(String(3), nullable=True)
    tone_match = Column(String(3), nullable=True)
    precision_score = Column(SmallInteger, nullable=True)
    student_failure_mode_key = Column(String(100), nullable=True)
    distractor_distance = Column(String(50), nullable=True)
    distractor_competition_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="options", foreign_keys=[question_id])


class QuestionAsset(Base):
    __tablename__ = "question_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    content_origin = Column(Enum(*CONTENT_ORIGINS, name="content_origin_enum"), nullable=False)
    asset_type = Column(Enum(*ASSET_TYPES, name="asset_type_enum"), nullable=False)
    storage_path = Column(Text, nullable=False)
    mime_type = Column(String(100), nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    source_url = Column(Text, nullable=True)
    source_name = Column(String(200), nullable=True)
    source_exam_code = Column(String(20), nullable=True)
    source_subject_code = Column(String(10), nullable=True)
    source_section_code = Column(String(10), nullable=True)
    source_module_code = Column(String(10), nullable=True)
    source_question_number = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="assets", foreign_keys=[question_id])


class QuestionSourceSpan(Base):
    __tablename__ = "question_source_spans"
    __table_args__ = (
        Index("ix_question_source_spans_question_id", "question_id"),
        Index("ix_question_source_spans_job_id", "question_job_id"),
        Index("ix_question_source_spans_raw_asset_id", "raw_asset_id"),
        Index("ix_question_source_spans_region_role", "source_region_role"),
        Index("ix_question_source_spans_extraction_method", "extraction_method"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    question_job_id = Column(UUID(as_uuid=True), ForeignKey("question_jobs.id"), nullable=True)
    raw_asset_id = Column(UUID(as_uuid=True), ForeignKey("question_assets.id"), nullable=True)
    source_page_number = Column(Integer, nullable=False)
    source_region_role = Column(String(40), nullable=False)
    extraction_method = Column(String(50), nullable=False)
    rendered_page_path = Column(Text, nullable=True)
    crop_path = Column(Text, nullable=True)
    ocr_text_path = Column(Text, nullable=True)
    layout_json_path = Column(Text, nullable=True)
    pymupdf_text = Column(Text, nullable=True)
    ocr_text = Column(Text, nullable=True)
    diagnostics_jsonb = Column(JSONB, nullable=True)
    confidence_jsonb = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="source_spans", foreign_keys=[question_id])


class QuestionStimulusAsset(Base):
    __tablename__ = "question_stimulus_assets"
    __table_args__ = (
        Index("ix_question_stimulus_assets_question_id", "question_id"),
        Index("ix_question_stimulus_assets_job_id", "question_job_id"),
        Index("ix_question_stimulus_assets_raw_asset_id", "raw_asset_id"),
        Index("ix_question_stimulus_assets_source_span_id", "source_span_id"),
        Index("ix_question_stimulus_assets_type", "stimulus_type"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    question_job_id = Column(UUID(as_uuid=True), ForeignKey("question_jobs.id"), nullable=True)
    raw_asset_id = Column(UUID(as_uuid=True), ForeignKey("question_assets.id"), nullable=True)
    stimulus_type = Column(String(40), nullable=False)
    storage_path = Column(Text, nullable=False)
    source_page_number = Column(Integer, nullable=True)
    source_span_id = Column(UUID(as_uuid=True), ForeignKey("question_source_spans.id"), nullable=True)
    title = Column(Text, nullable=True)
    structured_data_jsonb = Column(JSONB, nullable=True)
    render_hints_jsonb = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="stimulus_assets", foreign_keys=[question_id])


class QuestionRelation(Base):
    __tablename__ = "question_relations"
    __table_args__ = (
        UniqueConstraint("from_question_id", "to_question_id", "relation_type", name="uq_question_relations_pair_type"),
        Index("ix_question_relations_from_question_id", "from_question_id"),
        Index("ix_question_relations_to_question_id", "to_question_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    to_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    relation_type = Column(Enum(*RELATION_TYPES, name="relation_type_enum"), nullable=False)
    relation_strength = Column(Float, nullable=True)
    detection_method = Column(Text, nullable=True)
    is_human_confirmed = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    from_question = relationship("Question", back_populates="outgoing_relations", foreign_keys=[from_question_id])
    to_question = relationship("Question", back_populates="incoming_relations", foreign_keys=[to_question_id])


class LlmEvaluation(Base):
    __tablename__ = "llm_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("question_jobs.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    task_type = Column(String(20), nullable=False)
    score_overall = Column(Float, nullable=True)
    score_metadata = Column(Float, nullable=True)
    score_explanation = Column(Float, nullable=True)
    score_generation = Column(Float, nullable=True)
    review_notes = Column(Text, nullable=True)
    recommended_for_default = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


# --- Generation factory (Phase 1) tables ---

class GenerationBatch(Base):
    __tablename__ = "generation_batches"
    __table_args__ = (
        Index("ix_generation_batches_status", "status"),
        Index("ix_generation_batches_student_id", "student_id"),
        Index("ix_generation_batches_requested_by_user_token", "requested_by_user_token"),
        Index("ix_generation_batches_requested_by_created_at", "requested_by", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requested_count = Column(Integer, nullable=False)
    request_jsonb = Column(JSONB, nullable=False)
    requested_by = Column(String(32), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    requested_by_user_token = Column(UUID(as_uuid=True), nullable=True)
    release_policy = Column(String(40), nullable=False, default="admin_review_required")
    regenerate_source_batch_id = Column(UUID(as_uuid=True), ForeignKey("generation_batches.id"), nullable=True)
    status = Column(String(40), nullable=False, default="pending")

    created_count = Column(Integer, nullable=False, default=0)
    accepted_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    needs_review_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GenerationBatchIdempotencyKey(Base):
    __tablename__ = "generation_batch_idempotency_keys"
    __table_args__ = (
        UniqueConstraint("idempotency_key", "requested_by",
                         name="uq_generation_batch_idem_per_requester"),
        Index("ix_generation_batch_idem_expires_at", "expires_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(128), nullable=False)
    requested_by = Column(String(32), nullable=False)
    generation_batch_id = Column(UUID(as_uuid=True),
                                 ForeignKey("generation_batches.id"),
                                 nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


# --- Review swarm tables (Phase 3) ---

class ReviewRun(Base):
    __tablename__ = "review_runs"
    __table_args__ = (
        Index("ix_review_runs_question_id", "question_id"),
        Index("ix_review_runs_status", "status"),
        Index("ix_review_runs_generation_batch_id", "generation_batch_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    generation_batch_id = Column(UUID(as_uuid=True), ForeignKey("generation_batches.id"), nullable=True)
    triggered_by = Column(Enum(*TRIGGERED_BY_VALUES, name="triggered_by_enum"), nullable=False)
    triggered_by_admin_token = Column(String(128), nullable=True)
    rubric_version = Column(String(20), nullable=False)
    rules_versions_jsonb = Column(JSONB, nullable=False, default=dict)
    status = Column(Enum(*REVIEW_RUN_STATUSES, name="review_run_status_enum"), nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class LlmReviewResult(Base):
    __tablename__ = "llm_review_results"
    __table_args__ = (
        Index("ix_llm_review_results_question_id", "question_id"),
        Index("ix_llm_review_results_review_run_id", "review_run_id"),
        Index("ix_llm_review_results_provider_model", "provider_name", "model_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("question_jobs.id"), nullable=True)
    generation_batch_id = Column(UUID(as_uuid=True), ForeignKey("generation_batches.id"), nullable=True)
    review_run_id = Column(UUID(as_uuid=True), ForeignKey("review_runs.id"), nullable=False)
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    task_type = Column(String(20), nullable=False, default="generation_realism_review")
    rubric_version = Column(String(20), nullable=False)
    rules_versions_jsonb = Column(JSONB, nullable=False, default=dict)
    scores_jsonb = Column(JSONB, nullable=False, default=dict)
    verdict = Column(Enum(*REVIEW_VERDICTS, name="verdict_enum"), nullable=False)
    review_notes = Column(Text, nullable=True)
    raw_response_jsonb = Column(JSONB, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    token_usage_jsonb = Column(JSONB, nullable=True)
    review_status = Column(Enum(*REVIEW_STATUSES, name="review_status_enum"), nullable=False, default="ok")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class ConsensusVerdict(Base):
    __tablename__ = "consensus_verdicts"
    __table_args__ = (
        Index("ix_consensus_verdicts_question_id", "question_id"),
        Index("ix_consensus_verdicts_review_run_id", "review_run_id"),
        Index("ix_consensus_verdicts_generation_batch_id", "generation_batch_id"),
        Index("ix_consensus_verdicts_consensus_verdict", "consensus_verdict"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    review_run_id = Column(UUID(as_uuid=True), ForeignKey("review_runs.id"), nullable=False)
    generation_batch_id = Column(UUID(as_uuid=True), ForeignKey("generation_batches.id"), nullable=True)
    reviewer_count = Column(Integer, nullable=False)
    average_realism = Column(Float, nullable=True)
    average_sat_fidelity = Column(Float, nullable=True)
    average_difficulty_match = Column(Float, nullable=True)
    average_distractor_quality = Column(Float, nullable=True)
    average_taxonomy_match = Column(Float, nullable=True)
    max_copy_risk = Column(Float, nullable=True)
    accept_votes = Column(Integer, nullable=False, default=0)
    needs_review_votes = Column(Integer, nullable=False, default=0)
    reject_votes = Column(Integer, nullable=False, default=0)
    reviewer_disagreement = Column(Float, nullable=True)
    high_disagreement_flag = Column(Boolean, nullable=False, default=False)
    consensus_verdict = Column(Enum(*CONSENSUS_VERDICTS, name="consensus_verdict_enum"), nullable=False)
    reasons_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class ReviewerAdminOverride(Base):
    __tablename__ = "reviewer_admin_overrides"
    __table_args__ = (
        UniqueConstraint(
            "admin_decision_id",
            "llm_review_result_id",
            name="uq_reviewer_admin_override_decision_result",
        ),
        Index("ix_reviewer_admin_overrides_question_id", "question_id"),
        Index("ix_reviewer_admin_overrides_llm_review_result_id", "llm_review_result_id"),
        Index("ix_reviewer_admin_overrides_admin_decision_id", "admin_decision_id"),
        Index("ix_reviewer_admin_overrides_override_direction", "override_direction"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_decision_id = Column(UUID(as_uuid=True), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    llm_review_result_id = Column(UUID(as_uuid=True), ForeignKey("llm_review_results.id"), nullable=False)
    reviewer_verdict = Column(String(40), nullable=False)
    admin_verdict = Column(String(40), nullable=False)
    override_direction = Column(String(40), nullable=False)
    admin_token = Column(String(128), nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


# --- Segment B tables ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    user_token = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    progress_records = relationship("UserProgress", back_populates="user")


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        Index("ix_user_progress_user_id", "user_id"),
        Index("ix_user_progress_question_id", "question_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    selected_option_label = Column(String(1), nullable=False)
    missed_grammar_focus_key = Column(String(50), nullable=True)
    missed_syntactic_trap_key = Column(String(50), nullable=True)
    # Phase 8: denormalized target dimensions for weakness profile
    missed_reading_focus_key = Column(String(100), nullable=True)
    missed_reading_skill_family_key = Column(String(100), nullable=True)
    question_domain = Column(String(20), nullable=True, index=True)
    question_difficulty = Column(String(20), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, index=True)

    user = relationship("User", back_populates="progress_records")
    question = relationship("Question", back_populates="progress_records", foreign_keys=[question_id])
