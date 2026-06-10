from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class InstallerInfo(BaseModel):
    id: str
    employee_id: Optional[int]
    full_name: str


class SessionInfo(BaseModel):
    id: str
    score_pct: int
    correct_cnt: int
    total_cnt: int
    duration_sec: int
    submitted_at: datetime


class PendingApprovalItem(BaseModel):
    daily_access_id: str
    installer: InstallerInfo
    session: SessionInfo


class ApproveResponse(BaseModel):
    permit_id: str
    generated_at: datetime
    wfm_synced: bool


class RejectRequest(BaseModel):
    reason: Optional[str] = None


class RejectResponse(BaseModel):
    daily_access_id: str
    status: str


class HistoryItem(BaseModel):
    daily_access_id: str
    installer_full_name: str
    status: str
    score_pct: Optional[int]
    decided_at: Optional[datetime]
    permit_id: Optional[str]
