from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class QuestionCreate(BaseModel):
    text: str
    options: list[str]
    correct: int
    is_active: bool = True

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        if len(v) > 1000:
            raise ValueError("text must be <= 1000 chars")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        if len(v) < 2 or len(v) > 6:
            raise ValueError("options must have 2–6 items")
        for opt in v:
            if not opt.strip():
                raise ValueError("option must not be empty")
        return v

    @field_validator("correct")
    @classmethod
    def correct_in_range(cls, v: int, info) -> int:
        opts = info.data.get("options", [])
        if opts and not (0 <= v < len(opts)):
            raise ValueError("correct index out of range")
        return v


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    options: Optional[list[str]] = None
    correct: Optional[int] = None
    is_active: Optional[bool] = None


class QuestionOut(BaseModel):
    id: str
    text: str
    options: list[str]
    correct: int
    is_active: bool
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionDeleteResponse(BaseModel):
    id: str
    is_active: bool
    active_questions_remaining: int
    warning: Optional[str] = None
