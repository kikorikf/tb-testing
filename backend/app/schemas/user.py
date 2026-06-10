from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    keycloak_id: str
    employee_id: Optional[int]
    full_name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
