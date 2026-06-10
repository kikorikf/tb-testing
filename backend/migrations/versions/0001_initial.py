"""initial schema + seed questions

Revision ID: 0001
Revises:
Create Date: 2026-06-10
"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("keycloak_id", sa.String(255), nullable=False, unique=True),
        sa.Column("employee_id", sa.Integer, nullable=True, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('installer', 'engineer')", name="users_role_check"),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("options", JSONB, nullable=False),
        sa.Column("correct", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "test_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("installer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_date", sa.Date, nullable=False, server_default=sa.func.current_date()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="in_progress"),
        sa.Column("score_pct", sa.Integer, nullable=True),
        sa.Column("correct_cnt", sa.Integer, nullable=True),
        sa.Column("total_cnt", sa.Integer, nullable=True),
        sa.Column("duration_sec", sa.Integer, nullable=True),
        sa.Column("answers", JSONB, nullable=True),
        sa.Column("shuffled_options", JSONB, nullable=True),
        sa.CheckConstraint(
            "status IN ('in_progress', 'passed', 'failed', 'timed_out')",
            name="test_sessions_status_check",
        ),
    )
    op.create_index("ix_test_sessions_installer_date", "test_sessions", ["installer_id", "session_date"])

    op.create_table(
        "daily_access",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("installer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("access_date", sa.Date, nullable=False, server_default=sa.func.current_date()),
        sa.Column("status", sa.String(30), nullable=False, server_default="locked"),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("test_sessions.id"), nullable=True),
        sa.Column("engineer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("installer_id", "access_date", name="daily_access_unique"),
        sa.CheckConstraint(
            "status IN ('locked', 'pending_approval', 'approved', 'rejected')",
            name="daily_access_status_check",
        ),
    )

    op.create_table(
        "permits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("permit_id", sa.String(100), unique=True, nullable=False),
        sa.Column("installer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("engineer_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("test_sessions.id"), nullable=False),
        sa.Column("permit_date", sa.Date, nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("payload", JSONB, nullable=False),
    )
    op.create_index("ix_permits_installer_date", "permits", ["installer_id", "permit_date"])
    op.create_index("ix_permits_engineer_date", "permits", ["engineer_id", "permit_date"])

    # Seed questions
    seed_questions = [
        {
            "id": str(uuid.uuid4()),
            "text": "Что необходимо сделать перед началом работы с электроустановкой?",
            "options": ["Надеть СИЗ и проверить инструмент", "Сразу приступить к работе", "Позвонить мастеру", "Подождать 10 минут"],
            "correct": 0,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Какой минимальный класс защиты диэлектрических перчаток для работы до 1000 В?",
            "options": ["Класс 0", "Класс 1", "Класс 2", "Класс 3"],
            "correct": 0,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "При работе на высоте более скольких метров обязательно использование страховочной привязи?",
            "options": ["0,5 м", "1,0 м", "1,8 м", "2,0 м"],
            "correct": 2,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Что запрещено делать при работе в электроустановках без наряда-допуска?",
            "options": [
                "Проводить плановые работы",
                "Проводить аварийно-восстановительные работы",
                "Выполнять работы в условиях воздействия патогенов",
                "Проводить любые работы",
            ],
            "correct": 3,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Какова периодичность проверки знаний правил охраны труда для электротехнического персонала?",
            "options": ["Каждые 6 месяцев", "1 раз в год", "1 раз в 3 года", "1 раз в 5 лет"],
            "correct": 1,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Что необходимо сделать перед подъёмом на лестницу-стремянку?",
            "options": [
                "Убедиться, что лестница исправна и надёжно установлена",
                "Позвонить руководителю",
                "Надеть каску",
                "Записать в журнал инструктажа",
            ],
            "correct": 0,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Какое напряжение считается безопасным для переносных электрических светильников?",
            "options": ["12 В", "36 В", "110 В", "220 В"],
            "correct": 1,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "При какой концентрации кислорода в воздухе рабочей зоны запрещается работа без изолирующего СИЗОД?",
            "options": ["Менее 25%", "Менее 20%", "Менее 18%", "Менее 16%"],
            "correct": 2,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Что является основным документом, разрешающим производство работ повышенной опасности?",
            "options": ["Устное разрешение руководителя", "Наряд-допуск", "Запись в журнале", "Приказ директора"],
            "correct": 1,
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Как часто должны проходить инструктаж по пожарной безопасности работники на рабочем месте?",
            "options": ["Ежедневно", "Ежемесячно", "Каждые 6 месяцев", "1 раз в год"],
            "correct": 2,
        },
    ]

    questions_table = sa.table(
        "questions",
        sa.column("id", sa.String),
        sa.column("text", sa.Text),
        sa.column("options", JSONB),
        sa.column("correct", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(questions_table, seed_questions)


def downgrade() -> None:
    op.drop_table("permits")
    op.drop_table("daily_access")
    op.drop_table("test_sessions")
    op.drop_table("questions")
    op.drop_table("users")
