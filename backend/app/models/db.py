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
)

def _utcnow():
    return datetime.now(timezone.utc)


class QuestionJob(Base):
    __tablename__ = "question_jobs"
    __table_args__ = (
        Index("ix_question_jobs_status", "status"),
        Index("ix_question_jobs_created_at", "created_at"),
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
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    question = relationship("Question", back_populates="jobs", foreign_keys=[question_id])


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
    stimulus_mode_key = Column(String(30), nullable=True)
    stem_type_key = Column(String(40), nullable=True)
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
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    jobs = relationship("QuestionJob", back_populates="question", foreign_keys="[QuestionJob.question_id]")
    versions = relationship("QuestionVersion", back_populates="question", order_by="QuestionVersion.version_number", foreign_keys="[QuestionVersion.question_id]")
    annotations = relationship("QuestionAnnotation", back_populates="question", foreign_keys="[QuestionAnnotation.question_id]")
    options = relationship("QuestionOption", back_populates="question", order_by="QuestionOption.option_label", foreign_keys="[QuestionOption.question_id]")
    assets = relationship("QuestionAsset", back_populates="question", foreign_keys="[QuestionAsset.question_id]")
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
    distractor_type_key = Column(String(30), nullable=True)
    semantic_relation_key = Column(String(40), nullable=True)
    plausibility_source_key = Column(String(30), nullable=True)
    option_error_focus_key = Column(String(40), nullable=True)
    why_plausible = Column(Text, nullable=True)
    why_wrong = Column(Text, nullable=True)
    grammar_fit = Column(String(3), nullable=True)
    tone_match = Column(String(3), nullable=True)
    precision_score = Column(SmallInteger, nullable=True)
    student_failure_mode_key = Column(String(30), nullable=True)
    distractor_distance = Column(String(10), nullable=True)
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


# --- Segment B tables ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
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
    timestamp = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="progress_records")
    question = relationship("Question", back_populates="progress_records", foreign_keys=[question_id])
