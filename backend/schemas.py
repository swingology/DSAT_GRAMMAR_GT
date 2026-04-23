from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class QuestionBase(BaseModel):
    id: str
    source_type: str
    grammar_focus_key: str
    content: Dict[str, Any]

    class Config:
        from_attributes = True

class UserProgressCreate(BaseModel):
    user_id: int
    question_id: str
    is_correct: bool
    selected_option_label: str
    missed_grammar_focus_key: Optional[str] = None
    missed_syntactic_trap_key: Optional[str] = None

class UserStats(BaseModel):
    total_answered: int
    total_correct: int
    accuracy: float
    top_missed_focus_keys: List[str]
    top_missed_trap_keys: List[str]
