from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class QuestionOut(BaseModel):
    id: str
    text: str
    options: list[str]


class TestStartResponse(BaseModel):
    session_id: str
    started_at: datetime
    expires_at: datetime
    questions: list[QuestionOut]


class SubmitRequest(BaseModel):
    session_id: str
    answers: dict[str, int]


class SubmitResponse(BaseModel):
    session_id: str
    status: str
    score_pct: int
    correct_cnt: int
    total_cnt: int
    duration_sec: int
    passed: bool


class TestStatusResponse(BaseModel):
    date: date
    status: str
    session_id: Optional[str]
    score_pct: Optional[int]
    permit_id: Optional[str]
