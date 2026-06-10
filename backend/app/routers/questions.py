from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import CurrentUser, require_engineer
from app.db.models import Question, User
from app.db.session import get_db
from app.schemas.question import (
    QuestionCreate, QuestionDeleteResponse, QuestionOut, QuestionUpdate,
)
from app.services.question_service import count_active, will_be_below_minimum

router = APIRouter(prefix="/questions", tags=["questions"])


async def _get_engineer_user(db: AsyncSession, current_user: CurrentUser) -> User:
    result = await db.execute(select(User).where(User.keycloak_id == current_user.sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    return user


@router.get("", response_model=list[QuestionOut])
async def list_questions(
    is_active: Optional[bool] = None,
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    query = select(Question)
    if is_active is not None:
        query = query.where(Question.is_active == is_active)
    query = query.order_by(Question.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=QuestionOut, status_code=201)
async def create_question(
    body: QuestionCreate,
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_engineer_user(db, current_user)
    q = Question(
        text=body.text,
        options=body.options,
        correct=body.correct,
        is_active=body.is_active,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(q)
    await db.commit()
    await db.refresh(q)
    return q


@router.get("/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if q is None:
        raise HTTPException(404, "Not found")
    return q


@router.patch("/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: str,
    body: QuestionUpdate,
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_engineer_user(db, current_user)
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if q is None:
        raise HTTPException(404, "Not found")

    if body.options is not None:
        new_options = body.options
        new_correct = body.correct if body.correct is not None else q.correct
        if not (0 <= new_correct < len(new_options)):
            raise HTTPException(422, "correct index out of range for new options")
        q.options = new_options
        q.correct = new_correct
    elif body.correct is not None:
        if not (0 <= body.correct < len(q.options)):
            raise HTTPException(422, "correct index out of range")
        q.correct = body.correct

    if body.text is not None:
        q.text = body.text
    if body.is_active is not None:
        q.is_active = body.is_active
    q.updated_by = user.id

    await db.commit()
    await db.refresh(q)
    return q


@router.delete("/{question_id}", response_model=QuestionDeleteResponse)
async def deactivate_question(
    question_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if q is None:
        raise HTTPException(404, "Not found")

    active_count = await count_active(db)
    q.is_active = False
    await db.commit()

    remaining = active_count - 1
    warning = None
    if will_be_below_minimum(active_count):
        warning = f"Активных вопросов меньше минимума ({settings.test_min_questions}). Тест временно недоступен."

    return QuestionDeleteResponse(
        id=q.id,
        is_active=False,
        active_questions_remaining=remaining,
        warning=warning,
    )
