from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import UserOut

router = APIRouter(prefix="/me", tags=["auth"])


@router.get("", response_model=UserOut)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.keycloak_id == current_user.sub))
    user = result.scalar_one_or_none()
    if user is None:
        role = "engineer" if current_user.is_engineer else "installer"
        user = User(
            keycloak_id=current_user.sub,
            employee_id=current_user.employee_id,
            full_name=current_user.full_name,
            role=role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
