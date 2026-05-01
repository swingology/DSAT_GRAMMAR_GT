"""Pass 2 Pydantic schema — Question annotation output."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from app.models.ontology import (
    GRAMMAR_ROLE_KEYS, GRAMMAR_FOCUS_KEYS, GRAMMAR_FOCUS_BY_ROLE,
    SYNTACTIC_TRAP_KEYS, DIFFICULTY_KEYS, FREQUENCY_BANDS,
    STUDENT_FAILURE_MODE_KEYS, PASSAGE_ARCHITECTURE_KEYS,
    DISTRACTOR_DISTANCE_KEYS, QUESTION_FAMILY_KEYS,
    READING_SKILL_FAMILY_KEYS, READING_FOCUS_KEYS,
)


class QuestionAnnotation(BaseModel):
    # Classification
    question_family_key: Optional[str] = None
    grammar_role_key: Optional[str] = None
    grammar_focus_key: Optional[str] = None
    secondary_grammar_focus_keys: List[str] = Field(default_factory=list)
    skill_family: Optional[str] = None
    subskill: Optional[str] = None
    skill_family_key: Optional[str] = None
    reading_focus_key: Optional[str] = None
    secondary_reading_focus_keys: List[str] = Field(default_factory=list)
    reasoning_trap_key: Optional[str] = None
    transition_subtype_key: Optional[str] = None
    syntactic_trap_key: str = "none"
    difficulty_overall: str
    distractor_strength: Optional[str] = None
    topic_broad: Optional[str] = None
    topic_fine: Optional[str] = None
    evidence_scope_key: Optional[str] = None
    evidence_location_key: Optional[str] = None
    answer_mechanism_key: Optional[str] = None
    solver_pattern_key: Optional[str] = None
    reading_scope: Optional[str] = None
    reasoning_demand: Optional[str] = None
    register_label: Optional[str] = Field(default=None, alias="register")
    tone: Optional[str] = None
    difficulty_reading: Optional[str] = None
    difficulty_grammar: Optional[str] = None
    difficulty_inference: Optional[str] = None
    difficulty_vocab: Optional[str] = None
    disambiguation_rule_applied: Optional[str] = None
    classification_rationale: Optional[str] = None

    # Explanations
    explanation_short: str = Field(max_length=300)
    explanation_full: str = Field(max_length=2000)
    evidence_span_text: Optional[str] = None

    # Confidence / review
    annotation_confidence: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    review_notes: Optional[str] = None

    # V3 §21-29 extensions (optional for MVP)
    distractor_distance: Optional[str] = None
    distractor_competition_score: Optional[float] = None
    plausible_wrong_count: Optional[int] = None
    answer_separation_strength: Optional[str] = None
    passage_architecture_key: Optional[str] = None
    official_similarity_score: Optional[float] = None
    structural_similarity_score: Optional[float] = None
    empirical_difficulty_estimate: Optional[float] = None

    @field_validator("grammar_focus_key")
    @classmethod
    def validate_focus_key(cls, v):
        if v and v not in GRAMMAR_FOCUS_KEYS:
            raise ValueError(f"Invalid grammar_focus_key: {v}")
        return v

    @field_validator("syntactic_trap_key")
    @classmethod
    def validate_trap_key(cls, v):
        if v not in SYNTACTIC_TRAP_KEYS:
            raise ValueError(f"Invalid syntactic_trap_key: {v}")
        return v

    @field_validator("difficulty_overall")
    @classmethod
    def validate_difficulty(cls, v):
        if v not in DIFFICULTY_KEYS:
            raise ValueError(f"Invalid difficulty: {v}")
        return v

    @field_validator("grammar_role_key")
    @classmethod
    def validate_role_key(cls, v):
        if v and v not in GRAMMAR_ROLE_KEYS:
            raise ValueError(f"Invalid grammar_role_key: {v}")
        return v

    @field_validator("question_family_key")
    @classmethod
    def validate_question_family_key(cls, v):
        if v and v not in QUESTION_FAMILY_KEYS:
            raise ValueError(f"Invalid question_family_key: {v}")
        return v

    @field_validator("skill_family_key")
    @classmethod
    def validate_skill_family_key(cls, v):
        if v and v not in READING_SKILL_FAMILY_KEYS:
            raise ValueError(f"Invalid skill_family_key: {v}")
        return v

    @field_validator("reading_focus_key")
    @classmethod
    def validate_reading_focus_key(cls, v):
        if v and v not in READING_FOCUS_KEYS:
            raise ValueError(f"Invalid reading_focus_key: {v}")
        return v

    model_config = {"populate_by_name": True}

    @field_validator("distractor_distance")
    @classmethod
    def validate_distractor_distance(cls, v):
        if v and v not in DISTRACTOR_DISTANCE_KEYS:
            raise ValueError(f"Invalid distractor_distance: {v}")
        return v

    @field_validator("passage_architecture_key")
    @classmethod
    def validate_passage_arch(cls, v):
        if v and v not in PASSAGE_ARCHITECTURE_KEYS:
            raise ValueError(f"Invalid passage_architecture_key: {v}")
        return v
