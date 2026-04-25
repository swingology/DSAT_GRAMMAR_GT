"""HTTP request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class QuestionRecallResponse(BaseModel):
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
    source_module_code: Optional[str] = None
    latest_annotation: Optional[dict] = None
    options: List[dict] = Field(default_factory=list)
    lineage: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserProgressCreate(BaseModel):
    user_id: int
    question_id: str
    is_correct: bool
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


class GenerationRequest(BaseModel):
    target_grammar_role_key: str
    target_grammar_focus_key: str
    target_syntactic_trap_key: str = "none"
    difficulty_overall: str = "medium"
    source_question_ids: Optional[List[str]] = None
    provider_name: Optional[str] = None
    model_name: Optional[str] = None


class GenerationCompareRequest(BaseModel):
    target_grammar_role_key: str
    target_grammar_focus_key: str
    target_syntactic_trap_key: str = "none"
    difficulty_overall: str = "medium"
    providers: List[str] = Field(default_factory=lambda: ["anthropic"])
    source_question_ids: Optional[List[str]] = None


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    question_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReannotateRequest(BaseModel):
    provider_name: str = "anthropic"
    model_name: str = "claude-sonnet-4-6"