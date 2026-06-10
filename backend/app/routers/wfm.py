from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, require_installer
from app.db.models import DailyAccess, User
from app.db.session import get_db
from app.services import wfm_client

router = APIRouter(prefix="/wfm", tags=["wfm"])


@router.get("/shifts")
async def get_shifts(
    shift_date: Optional[str] = None,
    current_user: CurrentUser = Depends(require_installer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.keycloak_id == current_user.sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")

    today = date.today()
    access_result = await db.execute(
        select(DailyAccess).where(
            DailyAccess.installer_id == user.id,
            DailyAccess.access_date == today,
        )
    )
    access = access_result.scalar_one_or_none()
    if not access or access.status != "approved":
        raise HTTPException(403, "Access not approved today")

    date_str = shift_date or today.strftime("%Y%m%d")
    try:
        return await wfm_client.get_shifts(user.employee_id, date_str)
    except Exception as e:
        raise HTTPException(502, f"WFM API error: {e}")
