import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import DailyAccess, Question, TestSession
from app.schemas.test import QuestionOut, SubmitResponse, TestStartResponse


async def get_or_create_daily_access(session: AsyncSession, installer_id: str) -> DailyAccess:
    today = date.today()
    result = await session.execute(
        select(DailyAccess).where(
            DailyAccess.installer_id == installer_id,
            DailyAccess.access_date == today,
        )
    )
    access = result.scalar_one_or_none()
    if access is None:
        access = DailyAccess(installer_id=installer_id, access_date=today, status="locked")
        session.add(access)
        await session.flush()
    return access


async def start_test(session: AsyncSession, installer_id: str) -> TestStartResponse:
    access = await get_or_create_daily_access(session, installer_id)
    if access.status == "approved":
        raise ValueError("already_approved")
    if access.status == "pending_approval":
        raise ValueError("pending_approval")

    result = await session.execute(
        select(Question).where(Question.is_active == True)
    )
    questions = result.scalars().all()
    if len(questions) < settings.test_min_questions:
        raise ValueError("not_enough_questions")

    shuffled_qs = list(questions)
    random.shuffle(shuffled_qs)

    shuffled_options_map: dict[str, list[int]] = {}
    questions_out: list[QuestionOut] = []

    for q in shuffled_qs:
        indices = list(range(len(q.options)))
        random.shuffle(indices)
        shuffled_options_map[q.id] = indices
        options_shuffled = [q.options[i] for i in indices]
        questions_out.append(QuestionOut(id=q.id, text=q.text, options=options_shuffled))

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.test_timer_seconds)

    test_session = TestSession(
        installer_id=installer_id,
        session_date=date.today(),
        started_at=now,
        status="in_progress",
        shuffled_options=shuffled_options_map,
    )
    session.add(test_session)

    access.session_id = test_session.id
    await session.commit()
    await session.refresh(test_session)

    return TestStartResponse(
        session_id=test_session.id,
        started_at=now,
        expires_at=expires_at,
        questions=questions_out,
    )


async def submit_test(
    session: AsyncSession, installer_id: str, session_id: str, answers: dict[str, int]
) -> SubmitResponse:
    result = await session.execute(
        select(TestSession).where(TestSession.id == session_id)
    )
    test_session = result.scalar_one_or_none()
    if test_session is None:
        raise LookupError("session_not_found")
    if test_session.installer_id != installer_id:
        raise PermissionError("forbidden")
    if test_session.status != "in_progress":
        raise ValueError("already_submitted")

    now = datetime.now(timezone.utc)
    expires_at = test_session.started_at + timedelta(seconds=settings.test_timer_seconds)
    if now > expires_at:
        test_session.status = "timed_out"
        test_session.submitted_at = now
        test_session.score_pct = 0
        test_session.correct_cnt = 0
        test_session.total_cnt = len(test_session.shuffled_options or {})
        test_session.duration_sec = settings.test_timer_seconds
        await session.commit()
        raise TimeoutError("session_expired")

    shuffled_options: dict[str, list[int]] = test_session.shuffled_options or {}
    q_ids = list(shuffled_options.keys())

    qs_result = await session.execute(
        select(Question).where(Question.id.in_(q_ids))
    )
    questions_map = {q.id: q for q in qs_result.scalars().all()}

    correct_cnt = 0
    total_cnt = len(q_ids)

    for q_id in q_ids:
        if q_id not in questions_map:
            continue
        q = questions_map[q_id]
        shuffled_idx_map = shuffled_options[q_id]
        given_shuffled_idx = answers.get(q_id)
        if given_shuffled_idx is None:
            continue
        if 0 <= given_shuffled_idx < len(shuffled_idx_map):
            original_idx = shuffled_idx_map[given_shuffled_idx]
            if original_idx == q.correct:
                correct_cnt += 1

    duration_sec = int((now - test_session.started_at).total_seconds())
    score_pct = round(correct_cnt / total_cnt * 100) if total_cnt else 0
    passed = score_pct >= settings.test_pass_threshold
    status = "passed" if passed else "failed"

    test_session.submitted_at = now
    test_session.status = status
    test_session.score_pct = score_pct
    test_session.correct_cnt = correct_cnt
    test_session.total_cnt = total_cnt
    test_session.duration_sec = duration_sec
    test_session.answers = answers

    if passed:
        access = await get_or_create_daily_access(session, installer_id)
        access.status = "pending_approval"
        access.session_id = test_session.id

    await session.commit()

    return SubmitResponse(
        session_id=session_id,
        status=status,
        score_pct=score_pct,
        correct_cnt=correct_cnt,
        total_cnt=total_cnt,
        duration_sec=duration_sec,
        passed=passed,
    )
