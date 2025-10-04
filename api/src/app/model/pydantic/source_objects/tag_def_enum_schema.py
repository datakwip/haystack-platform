from pydantic import BaseModel
from typing import Optional
import datetime

class TagDefEnumBase(BaseModel):
    value : str
    label : str
    disabled_ts : Optional[datetime.datetime]

class TagDefEnumRelationCreate(TagDefEnumBase):
    pass

class TagDefEnum(TagDefEnumBase):
    id : int
    tag_id : int
    class Config:
        orm_mode = True

class TagDefEnumCreate(TagDefEnumRelationCreate):
    org_id : int
    tag_name : str
    class Config:
        orm_mode = True

class TagDefEnumUpdate(TagDefEnumRelationCreate):
    org_id : int

    class Config:
        orm_mode = True

class TagDefEnumDelete(BaseModel):
    org_id : int