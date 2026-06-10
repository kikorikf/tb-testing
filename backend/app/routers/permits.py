from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import Permit, User
from app.db.session import get_db
from app.schemas.permit import PermitOut

router = APIRouter(prefix="/permits", tags=["permits"])


async def _get_user(db: AsyncSession, current_user: CurrentUser) -> User:
    result = await db.execute(select(User).where(User.keycloak_id == current_user.sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "User not found")
    return user


@router.get("/my", response_model=list[PermitOut])
async def my_permits(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, current_user)
    query = select(Permit)
    if user.role == "installer":
        query = query.where(Permit.installer_id == user.id)
    else:
        query = query.where(Permit.engineer_id == user.id)
    if date_from:
        query = query.where(Permit.permit_date >= date_from)
    if date_to:
        query = query.where(Permit.permit_date <= date_to)
    query = query.order_by(Permit.permit_date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/my/{permit_id}", response_model=PermitOut)
async def get_permit(
    permit_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, current_user)
    result = await db.execute(select(Permit).where(Permit.permit_id == permit_id))
    permit = result.scalar_one_or_none()
    if permit is None:
        raise HTTPException(404, "Not found")
    if user.role == "installer" and permit.installer_id != user.id:
        raise HTTPException(404, "Not found")
    if user.role == "engineer" and permit.engineer_id != user.id:
        raise HTTPException(404, "Not found")
    return permit
