from datetime import date, timedelta, timezone, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import CurrentUser, require_installer
from app.db.models import DailyAccess, Permit, TestSession, User
from app.db.session import get_db
from app.schemas.test import (
    SubmitRequest, SubmitResponse, TestStartResponse, TestStatusResponse,
)
from app.services import test_service

router = APIRouter(prefix="/test", tags=["test"])


async def _get_db_user(db: AsyncSession, current_user: CurrentUser) -> User:
    result = await db.execute(select(User).where(User.keycloak_id == current_user.sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found; call GET /me first")
    return user


@router.get("/status", response_model=TestStatusResponse)
async def test_status(
    current_user: CurrentUser = Depends(require_installer),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_db_user(db, current_user)
    today = date.today()
    result = await db.execute(
        select(DailyAccess).where(
            DailyAccess.installer_id == user.id,
            DailyAccess.access_date == today,
        )
    )
    access = result.scalar_one_or_none()
    if access is None:
        return TestStatusResponse(date=today, status="locked", session_id=None, score_pct=None, permit_id=None)

    permit_id = None
    if access.status == "approved" and access.session_id:
        p_result = await db.execute(
            select(Permit).where(Permit.session_id == access.session_id)
        )
        permit = p_result.scalar_one_or_none()
        if permit:
            permit_id = permit.permit_id

    score_pct = None
    if access.session_id:
        s_result = await db.execute(select(TestSession).where(TestSession.id == access.session_id))
        ts = s_result.scalar_one_or_none()
        if ts:
            score_pct = ts.score_pct

    return TestStatusResponse(
        date=today,
        status=access.status,
        session_id=access.session_id,
        score_pct=score_pct,
        permit_id=permit_id,
    )


@router.post("/start", response_model=TestStartResponse, status_code=201)
async def start_test(
    current_user: CurrentUser = Depends(require_installer),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_db_user(db, current_user)
    try:
        return await test_service.start_test(db, user.id)
    except ValueError as e:
        msg = str(e)
        if msg == "already_approved":
            raise HTTPException(409, "Already approved today")
        if msg == "pending_approval":
            raise HTTPException(409, "Already pending approval")
        if msg == "not_enough_questions":
            raise HTTPException(422, f"Not enough active questions (min {settings.test_min_questions})")
        raise HTTPException(400, msg)


@router.post("/submit", response_model=SubmitResponse)
async def submit_test(
    body: SubmitRequest,
    current_user: CurrentUser = Depends(require_installer),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_db_user(db, current_user)
    try:
        return await test_service.submit_test(db, user.id, body.session_id, body.answers)
    except LookupError:
        raise HTTPException(404, "Session not found")
    except PermissionError:
        raise HTTPException(403, "Forbidden")
    except TimeoutError:
        raise HTTPException(410, "Session expired")
    except ValueError as e:
        raise HTTPException(409, str(e))
