from typing import Optional, List, Dict
from pydantic import BaseModel
import datetime


class FilterRequest(BaseModel):
    filter: str
    tag:Optional[str]
    tags: Optional[list]
    org_id: int


class FilterResponse(BaseModel):
    entity_id: int
    tags: Optional[list]


class ReportFilterRequest(BaseModel):
    value: dict
    org: str
