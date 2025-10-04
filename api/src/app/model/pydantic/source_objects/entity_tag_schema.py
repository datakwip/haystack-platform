import datetime
import decimal

from pydantic import BaseModel, Json
from typing import Optional
from typing import Union
class EntityTagBase(BaseModel):
    value_n: Optional[decimal.Decimal]
    value_b: Optional[bool]
    value_s: Optional[str]
    value_ts: Optional[datetime.datetime]
    value_list: Optional[list]
    value_dict: Optional[Json]
    value_ref: Optional[Union[int, list[int]]]
    value_enum: Optional[int]

class EntityTagCreate(EntityTagBase):
    tag_name: str
    class Config:
        orm_mode = True



class EntityTag(EntityTagBase):
    id: int
    entity_id : int
    tag_id: int
    class Config:
        orm_mode = True

class EntityTagCreateWithEntityId(EntityTagCreate):
    org_id : int
    entity_id : int

class EntityTagUpdate(EntityTagBase):
    org_id : int
    class Config:
        orm_mode = True

class EntityTagDelete(BaseModel):
    org_id : int