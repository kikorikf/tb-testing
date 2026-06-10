from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, require_engineer
from app.db.models import DailyAccess, Permit, TestSession, User
from app.db.session import get_db
from app.schemas.approval import (
    ApproveResponse, HistoryItem, InstallerInfo, PendingApprovalItem,
    RejectRequest, RejectResponse, SessionInfo,
)
from app.services import permit_service
from app.services import wfm_client

router = APIRouter(prefix="/approvals", tags=["approvals"])


async def _get_engineer(db: AsyncSession, current_user: CurrentUser) -> User:
    result = await db.execute(select(User).where(User.keycloak_id == current_user.sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found; call GET /me first")
    return user


@router.get("/pending", response_model=list[PendingApprovalItem])
async def pending_approvals(
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    result = await db.execute(
        select(DailyAccess).where(
            DailyAccess.access_date == today,
            DailyAccess.status == "pending_approval",
        )
    )
    accesses = result.scalars().all()

    items = []
    for access in accesses:
        installer_res = await db.execute(select(User).where(User.id == access.installer_id))
        installer = installer_res.scalar_one_or_none()
        if not installer:
            continue
        session_res = await db.execute(select(TestSession).where(TestSession.id == access.session_id))
        ts = session_res.scalar_one_or_none()
        if not ts:
            continue
        items.append(
            PendingApprovalItem(
                daily_access_id=access.id,
                installer=InstallerInfo(
                    id=installer.id,
                    employee_id=installer.employee_id,
                    full_name=installer.full_name,
                ),
                session=SessionInfo(
                    id=ts.id,
                    score_pct=ts.score_pct or 0,
                    correct_cnt=ts.correct_cnt or 0,
                    total_cnt=ts.total_cnt or 0,
                    duration_sec=ts.duration_sec or 0,
                    submitted_at=ts.submitted_at or ts.started_at,
                ),
            )
        )
    return items


@router.post("/{daily_access_id}/approve", response_model=ApproveResponse)
async def approve(
    daily_access_id: str,
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    engineer = await _get_engineer(db, current_user)
    result = await db.execute(select(DailyAccess).where(DailyAccess.id == daily_access_id))
    access = result.scalar_one_or_none()
    if access is None:
        raise HTTPException(404, "Not found")
    if access.status != "pending_approval":
        raise HTTPException(409, "Already resolved")

    installer_res = await db.execute(select(User).where(User.id == access.installer_id))
    installer = installer_res.scalar_one()
    session_res = await db.execute(select(TestSession).where(TestSession.id == access.session_id))
    ts = session_res.scalar_one()

    permit = await permit_service.generate_permit(db, access, installer, engineer, ts)

    access.status = "approved"
    access.engineer_id = engineer.id
    access.decided_at = datetime.now(timezone.utc)

    await db.flush()
    await db.commit()
    await db.refresh(permit)

    wfm_synced = False
    try:
        today_str = access.access_date.strftime("%Y%m%d")
        await wfm_client.post_shift(
            installer.employee_id,
            f"{access.access_date}T08:00:00.000Z",
            f"{access.access_date}T17:00:00.000Z",
        )
        wfm_synced = True
    except Exception:
        pass

    return ApproveResponse(
        permit_id=permit.permit_id,
        generated_at=permit.generated_at,
        wfm_synced=wfm_synced,
    )


@router.post("/{daily_access_id}/reject", response_model=RejectResponse)
async def reject(
    daily_access_id: str,
    body: RejectRequest,
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DailyAccess).where(DailyAccess.id == daily_access_id))
    access = result.scalar_one_or_none()
    if access is None:
        raise HTTPException(404, "Not found")
    if access.status != "pending_approval":
        raise HTTPException(409, "Already resolved")

    engineer = await _get_engineer(db, current_user)
    access.status = "rejected"
    access.engineer_id = engineer.id
    access.decided_at = datetime.now(timezone.utc)

    if access.session_id:
        session_res = await db.execute(select(TestSession).where(TestSession.id == access.session_id))
        ts = session_res.scalar_one_or_none()
        if ts:
            ts.status = "failed"

    access.session_id = None
    await db.commit()
    return RejectResponse(daily_access_id=daily_access_id, status="rejected")


@router.get("/history", response_model=list[HistoryItem])
async def history(
    current_user: CurrentUser = Depends(require_engineer),
    db: AsyncSession = Depends(get_db),
):
    engineer = await _get_engineer(db, current_user)
    today = date.today()
    result = await db.execute(
        select(DailyAccess).where(
            DailyAccess.access_date == today,
            DailyAccess.engineer_id == engineer.id,
            DailyAccess.status.in_(["approved", "rejected"]),
        )
    )
    accesses = result.scalars().all()

    items = []
    for access in accesses:
        installer_res = await db.execute(select(User).where(User.id == access.installer_id))
        installer = installer_res.scalar_one_or_none()
        score_pct = None
        permit_id = None
        if access.session_id:
            s_res = await db.execute(select(TestSession).where(TestSession.id == access.session_id))
            ts = s_res.scalar_one_or_none()
            if ts:
                score_pct = ts.score_pct
        if access.status == "approved":
            p_res = await db.execute(
                select(Permit).where(Permit.installer_id == access.installer_id, Permit.permit_date == today)
            )
            permit = p_res.scalar_one_or_none()
            if permit:
                permit_id = permit.permit_id

        items.append(
            HistoryItem(
                daily_access_id=access.id,
                installer_full_name=installer.full_name if installer else "",
                status=access.status,
                score_pct=score_pct,
                decided_at=access.decided_at,
                permit_id=permit_id,
            )
        )
    return items
