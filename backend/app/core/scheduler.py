import logging
from datetime import date

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import insert, select

from app.core.config import settings
from app.db.models import DailyAccess, User
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=settings.timezone)


async def daily_reset() -> None:
    logger.info("Running daily reset")
    today = date.today()
    async with async_session_factory() as session:
        result = await session.execute(
            select(User.id).where(User.role == "installer")
        )
        installer_ids = result.scalars().all()
        for installer_id in installer_ids:
            existing = await session.execute(
                select(DailyAccess).where(
                    DailyAccess.installer_id == installer_id,
                    DailyAccess.access_date == today,
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(
                    DailyAccess(
                        installer_id=installer_id,
                        access_date=today,
                        status="locked",
                    )
                )
        await session.commit()
    logger.info("Daily reset complete: %d installers", len(installer_ids))


def start_scheduler() -> None:
    tz = pytz.timezone(settings.timezone)
    scheduler.add_job(daily_reset, "cron", hour=0, minute=0, timezone=tz)
    scheduler.start()
