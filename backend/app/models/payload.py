"""HTTP request/response models."""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Any, Dict
from datetime import datetime


class StudentQuestionResponse(BaseModel):
    """Student-facing question payload — answer key excluded."""
    id: str
    content_origin: str
    current_question_text: str
    current_passage_text: Optional[str] = None
    practice_status: str
    grammar_focus_key: Optional[str] = None
    difficulty_overall: Optional[str] = None
    stimulus_mode_key: Optional[str] = None
    source_exam_code: Optional[str] = None
    source_subject_code: Optional[str] = None
    source_section_code: Optional[str] = None
    source_module_code: Optional[str] = None
    options: List[dict] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class QuestionRecallResponse(BaseModel):
    """Admin-facing recall payload — includes answer key."""
    id: str
    content_origin: str
    current_question_text: str
    current_passage_text: Optional[str] = None
    current_correct_option_label: str
    practice_status: str
    grammar_role_key: Optional[str] = None
    grammar_focus_key: Optional[str] = None
    difficulty_overall: Optional[str] = None
    stimulus_mode_key: Optional[str] = None
    source_exam_code: Optional[str] = None
    source_subject_code: Optional[str] = None
    source_section_code: Optional[str] = None
    source_module_code: Optional[str] = None
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
    source_exam_code: Optional[str] = None
    source_subject_code: Optional[str] = None
    source_section_code: Optional[str] = None
    source_module_code: Optional[str] = None
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
    user_token: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
