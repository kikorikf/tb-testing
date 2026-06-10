import uuid
from datetime import date, datetime

from sqlalchemy import (
    UUID, Boolean, CheckConstraint, Date, DateTime, ForeignKey,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def gen_uuid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    keycloak_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    employee_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('installer', 'engineer')", name="users_role_check"),
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSONB, nullable=False)
    correct: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TestSession(Base):
    __tablename__ = "test_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    installer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="in_progress")
    score_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_cnt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_cnt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    shuffled_options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'passed', 'failed', 'timed_out')",
            name="test_sessions_status_check",
        ),
    )


class DailyAccess(Base):
    __tablename__ = "daily_access"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    installer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    access_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="locked")
    session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("test_sessions.id"), nullable=True)
    engineer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("installer_id", "access_date", name="daily_access_unique"),
        CheckConstraint(
            "status IN ('locked', 'pending_approval', 'approved', 'rejected')",
            name="daily_access_status_check",
        ),
    )


class Permit(Base):
    __tablename__ = "permits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    permit_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    installer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_sessions.id"), nullable=False)
    permit_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
