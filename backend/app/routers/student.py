from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.auth import student_required, admin_required
from app.models.db import Question, User, UserProgress, QuestionAnnotation
from app.models.payload import QuestionRecallResponse, UserProgressCreate, UserStats

router = APIRouter(prefix="/api", tags=["student"])


@router.get("/questions", response_model=list[QuestionRecallResponse])
async def student_recall(
    grammar_focus: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    stmt = select(Question).where(Question.practice_status == "active")

    if origin:
        stmt = stmt.where(Question.content_origin == origin)

    if grammar_focus or difficulty:
        stmt = stmt.join(
            QuestionAnnotation,
            Question.latest_annotation_id == QuestionAnnotation.id,
        )
        if grammar_focus:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["grammar_focus_key"].astext == grammar_focus
            )
        if difficulty:
            stmt = stmt.where(
                QuestionAnnotation.annotation_jsonb["difficulty_overall"].astext == difficulty
            )

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    questions = result.unique().scalars().all()

    responses = []
    for q in questions:
        grammar_focus_key = None
        difficulty_overall = None
        if q.latest_annotation_id:
            ann = await db.get(QuestionAnnotation, q.latest_annotation_id)
            if ann:
                grammar_focus_key = ann.annotation_jsonb.get("grammar_focus_key")
                difficulty_overall = ann.annotation_jsonb.get("difficulty_overall")

        responses.append(QuestionRecallResponse(
            id=str(q.id),
            content_origin=q.content_origin,
            current_question_text=q.current_question_text,
            current_passage_text=q.current_passage_text,
            current_correct_option_label=q.current_correct_option_label,
            practice_status=q.practice_status,
            grammar_focus_key=grammar_focus_key,
            difficulty_overall=difficulty_overall,
            stimulus_mode_key=q.stimulus_mode_key,
            source_exam_code=q.source_exam_code,
        ))
    return responses


@router.post("/submit")
async def submit_answer(
    body: UserProgressCreate,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    try:
        qid = UUID(body.question_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid question_id")

    q = await db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    user = await db.get(User, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    progress = UserProgress(
        user_id=body.user_id,
        question_id=qid,
        is_correct=body.is_correct,
        selected_option_label=body.selected_option_label,
        missed_grammar_focus_key=body.missed_grammar_focus_key,
        missed_syntactic_trap_key=body.missed_syntactic_trap_key,
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return {"id": progress.id, "is_correct": progress.is_correct}


@router.get("/stats/{user_id}", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    result = await db.execute(
        select(UserProgress).where(UserProgress.user_id == user_id)
    )
    records = result.scalars().all()

    total = len(records)
    correct = sum(1 for r in records if r.is_correct)
    accuracy = correct / total if total > 0 else 0.0

    focus_counts = Counter(r.missed_grammar_focus_key for r in records if r.missed_grammar_focus_key and not r.is_correct)
    trap_counts = Counter(r.missed_syntactic_trap_key for r in records if r.missed_syntactic_trap_key and not r.is_correct)

    return UserStats(
        total_answered=total,
        total_correct=correct,
        accuracy=round(accuracy, 3),
        top_missed_focus_keys=[k for k, _ in focus_counts.most_common(5)],
        top_missed_trap_keys=[k for k, _ in trap_counts.most_common(5)],
    )


from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


@router.post("/users", response_model=UserResponse)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(username=body.username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(student_required),
):
    """Get a user by ID."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _auth: str = Depends(admin_required),
):
    """Delete a user and their progress records (admin only)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute(delete(UserProgress).where(UserProgress.user_id == user_id))
    await db.delete(user)
    await db.commit()
    return {"detail": "User deleted"}
