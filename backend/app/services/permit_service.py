from datetime import date, datetime, time, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DailyAccess, Permit, TestSession, User


def _make_permit_id(installer: User, permit_date: date) -> str:
    initials = "".join(
        part[0].upper()
        for part in installer.full_name.split()
        if part
    )[:3]
    return f"НД-{permit_date.strftime('%Y%m%d')}-{initials}"


async def generate_permit(
    session: AsyncSession,
    access: DailyAccess,
    installer: User,
    engineer: User,
    test_session: TestSession,
) -> Permit:
    today = date.today()
    valid_until = datetime.combine(today, time(23, 59, 59), tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    permit_id = _make_permit_id(installer, today)

    duration_sec = test_session.duration_sec or 0
    minutes, seconds = divmod(duration_sec, 60)
    duration_str = f"{minutes}м {seconds}с"

    payload = {
        "permit_id": permit_id,
        "date": today.isoformat(),
        "valid_until": valid_until.isoformat(),
        "generated_at": now.isoformat(),
        "installer": {
            "employee_id": installer.employee_id,
            "full_name": installer.full_name,
            "role": "installer",
        },
        "engineer": {
            "full_name": engineer.full_name,
            "role": "engineer",
        },
        "test_result": {
            "score_pct": test_session.score_pct,
            "correct_answers": test_session.correct_cnt,
            "total_questions": test_session.total_cnt,
            "duration": duration_str,
        },
        "wfm_access": {
            "unlocked": True,
            "shift_date": today.isoformat(),
            "employee_id": installer.employee_id,
        },
    }

    permit = Permit(
        permit_id=permit_id,
        installer_id=installer.id,
        engineer_id=engineer.id,
        session_id=test_session.id,
        permit_date=today,
        valid_until=valid_until,
        generated_at=now,
        payload=payload,
    )
    session.add(permit)
    return permit
