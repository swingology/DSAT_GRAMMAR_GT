"""Pass 1 Pydantic schema — Question extraction output."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from app.models.ontology import STIMULUS_MODE_KEYS, STEM_TYPE_KEYS


class ExtractedOption(BaseModel):
    label: str = Field(pattern=r"^[A-D]$")
    text: str


class QuestionExtract(BaseModel):
    question_text: str
    passage_text: Optional[str] = None
    paired_passage_text: Optional[str] = None
    options: List[ExtractedOption] = Field(min_length=4, max_length=4)
    correct_option_label: str = Field(pattern=r"^[A-D]$")
    source_exam_code: Optional[str] = None
    source_module_code: Optional[str] = None
    source_question_number: Optional[int] = None
    stimulus_mode_key: Optional[str] = None
    stem_type_key: Optional[str] = None
    table_data: Optional[dict] = None
    graph_data: Optional[dict] = None

    @field_validator("stimulus_mode_key")
    @classmethod
    def validate_stimulus(cls, v):
        if v and v not in STIMULUS_MODE_KEYS:
            raise ValueError(f"Invalid stimulus_mode_key: {v}")
        return v

    @field_validator("stem_type_key")
    @classmethod
    def validate_stem(cls, v):
        if v and v not in STEM_TYPE_KEYS:
            raise ValueError(f"Invalid stem_type_key: {v}")
        return v