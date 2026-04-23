from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, index=True) # Unique ID for the question
    source_type = Column(String, index=True) # e.g., "collegeBoard", "admin_uploaded", "llm_generated"
    grammar_focus_key = Column(String, index=True) # Indexed for targeted querying
    
    # The entire V3 JSON payload sits right here! 
    # Maximum flexibility without breaking the SQL schema.
    content = Column(JSON) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    is_correct = Column(Boolean)
    selected_option_label = Column(String) # e.g., "A", "B", "C", "D"
    
    # Storing these here prevents us from having to do complex JSON querying 
    # every time we want to calculate a user's weak spots.
    missed_grammar_focus_key = Column(String, nullable=True)
    missed_syntactic_trap_key = Column(String, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
