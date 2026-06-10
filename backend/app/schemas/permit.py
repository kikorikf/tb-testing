from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class PermitOut(BaseModel):
    permit_id: str
    permit_date: date
    valid_until: datetime
    generated_at: datetime
    payload: dict

    model_config = {"from_attributes": True}
