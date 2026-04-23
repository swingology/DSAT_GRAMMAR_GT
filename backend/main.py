from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db

# Automatically create the database tables based on our models
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DSAT Grammar API")

@app.get("/")
def read_root():
    return {"message": "DSAT Grammar API is running"}

@app.get("/api/questions", response_model=List[schemas.QuestionBase])
def get_questions(limit: int = 10, db: Session = Depends(get_db)):
    """Fetch a batch of questions from the database."""
    questions = db.query(models.Question).limit(limit).all()
    return questions

@app.post("/api/submit")
def submit_answer(progress: schemas.UserProgressCreate, db: Session = Depends(get_db)):
    """Record a user's answer and metadata about what they missed."""
    db_progress = models.UserProgress(**progress.model_dump())
    db.add(db_progress)
    db.commit()
    db.refresh(db_progress)
    return {"status": "success", "progress_id": db_progress.id}

@app.get("/api/stats/{user_id}", response_model=schemas.UserStats)
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """Calculate and return a user's top missed grammar keys and traps."""
    
    progress_records = db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).all()
    
    total = len(progress_records)
    if total == 0:
        return schemas.UserStats(
            total_answered=0, total_correct=0, accuracy=0.0,
            top_missed_focus_keys=[], top_missed_trap_keys=[]
        )
    
    correct = sum(1 for p in progress_records if p.is_correct)
    
    # Collect missed keys
    missed_focus = {}
    missed_traps = {}
    
    for p in progress_records:
        if not p.is_correct:
            if p.missed_grammar_focus_key:
                missed_focus[p.missed_grammar_focus_key] = missed_focus.get(p.missed_grammar_focus_key, 0) + 1
            if p.missed_syntactic_trap_key:
                missed_traps[p.missed_syntactic_trap_key] = missed_traps.get(p.missed_syntactic_trap_key, 0) + 1
                
    # Sort to find the top missed
    top_focus = sorted(missed_focus, key=missed_focus.get, reverse=True)[:3]
    top_traps = sorted(missed_traps, key=missed_traps.get, reverse=True)[:3]

    return schemas.UserStats(
        total_answered=total,
        total_correct=correct,
        accuracy=round((correct / total) * 100, 2),
        top_missed_focus_keys=top_focus,
        top_missed_trap_keys=top_traps
    )
