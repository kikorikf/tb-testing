from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Question


async def count_active(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count()).where(Question.is_active == True)
    )
    return result.scalar_one()


def will_be_below_minimum(active_count: int, delta: int = -1) -> bool:
    return (active_count + delta) < settings.test_min_questions
