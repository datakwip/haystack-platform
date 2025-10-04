from pydantic import BaseModel
from typing import Optional

class OrgBase(BaseModel):
    name : str
    key : Optional[str]
    value_table: str

class Org(OrgBase):
    id : int
    class Config:
        orm_mode = True

class OrgUpdate(BaseModel):
    name: Optional[str]
    key: Optional[str]
    value_table: Optional[str]
    class Config:
        orm_mode = True


class OrgCreate(OrgBase):
    class Config:
        orm_mode = True
