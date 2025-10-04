from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PollerConfigBase(BaseModel):
    poller_type: str
    poller_name: str
    config: str
    status: str

class PollerConfigCreate(PollerConfigBase):
    org_id: int

class PollerConfig(PollerConfigBase):
    id: int
    org_id: int
    poller_id: int
    created_at: datetime

    class Config:
        from_attributes = True