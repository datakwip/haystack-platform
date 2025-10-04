from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List

class FleetReportCreate(BaseModel):
    org_id: int
    device: str
    network: str 
    status: str
    attributes: Optional[Dict[str, Any]] = None
    onboarded: Optional[str] = None
    last_updated: Optional[str] = None


class FleetReport(FleetReportCreate):
    class Config:
        orm_mode = True
        
class FleetReportBulkItem(BaseModel):
    device: str
    network: str 
    status: str
    attributes: Optional[Dict[str, Any]] = None
    onboarded: Optional[str] = None
    last_updated: Optional[str] = None

class FleetReportBulkCreate(BaseModel):
    org_id: int
    reports: List[FleetReportBulkItem]