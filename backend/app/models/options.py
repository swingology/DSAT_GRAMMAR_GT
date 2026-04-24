"""Per-option Pydantic schema — V3 §10 option-level analysis."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.models.ontology import (
    DISTRACTOR_TYPE_KEYS, PLANSIBILITY_SOURCE_KEYS,
    STUDENT_FAILURE_MODE_KEYS, DISTRACTOR_DISTANCE_KEYS,
)


class OptionAnalysis(BaseModel):
    option_label: str = Field(pattern=r"^[A-D]$")
    option_text: str
    is_correct: bool
    option_role: str  # "correct" or "distractor"
    distractor_type_key: Optional[str] = None
    semantic_relation_key: Optional[str] = None
    plausibility_source_key: Optional[str] = None
    option_error_focus_key: Optional[str] = None
    why_plausible: Optional[str] = None
    why_wrong: Optional[str] = None
    grammar_fit: Optional[str] = None  # "yes" or "no"
    tone_match: Optional[str] = None    # "yes" or "no"
    precision_score: Optional[int] = Field(default=None, ge=1, le=3)
    student_failure_mode_key: Optional[str] = None
    distractor_distance: Optional[str] = None
    distractor_competition_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("distractor_type_key")
    @classmethod
    def validate_distractor_type(cls, v):
        if v and v not in DISTRACTOR_TYPE_KEYS:
            raise ValueError(f"Invalid distractor_type_key: {v}")
        return v

    @field_validator("plausibility_source_key")
    @classmethod
    def validate_plausibility(cls, v):
        if v and v not in PLANSIBILITY_SOURCE_KEYS:
            raise ValueError(f"Invalid plausibility_source_key: {v}")
        return v

    @field_validator("student_failure_mode_key")
    @classmethod
    def validate_failure_mode(cls, v):
        if v and v not in STUDENT_FAILURE_MODE_KEYS:
            raise ValueError(f"Invalid student_failure_mode_key: {v}")
        return v

    @field_validator("distractor_distance")
    @classmethod
    def validate_distractor_distance(cls, v):
        if v and v not in DISTRACTOR_DISTANCE_KEYS:
            raise ValueError(f"Invalid distractor_distance: {v}")
        return v

    @field_validator("grammar_fit")
    @classmethod
    def validate_grammar_fit(cls, v):
        if v and v not in ("yes", "no"):
            raise ValueError("grammar_fit must be 'yes' or 'no'")
        return v

    @field_validator("tone_match")
    @classmethod
    def validate_tone_match(cls, v):
        if v and v not in ("yes", "no"):
            raise ValueError("tone_match must be 'yes' or 'no'")
        return v