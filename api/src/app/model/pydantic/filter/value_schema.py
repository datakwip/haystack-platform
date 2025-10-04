from pydantic import BaseModel, Json
from typing import Optional
import datetime
import decimal
from app.model.pydantic.filter import filter_schema


class ValueBase(BaseModel):
    ts: Optional[datetime.datetime]
    time: Optional[datetime.datetime]
    entity_id: int
    value_n: Optional[decimal.Decimal]
    value_b: Optional[bool]
    value_s: Optional[str]
    value_ts: Optional[datetime.datetime]
    value_dict: Optional[Json]
    class Config:
        orm_mode = True

class ValueBaseResponse(BaseModel):
    ts: Optional[datetime.datetime]
    entity_id: int
    value_n: Optional[decimal.Decimal]
    value_b: Optional[bool]
    value_s: Optional[str]
    value_ts: Optional[datetime.datetime]
    value_dict: Optional[Json]
    class Config:
        orm_mode = True


class ValueBaseCreate(ValueBase):
    org_id: int

    class Config:
        orm_mode = True

class OperationRequest(BaseModel):
    aggregation: str
    time: str
    timeInSeconds: int

class ValueRequest(filter_schema.FilterRequest):
    date_from: str
    date_to: str
    val_tag: Optional[str]
    operation: OperationRequest

class Value(ValueBase):
    entity_id: int
    entity_name: str
    kind: str

class ValueBulkCreate(BaseModel):
    org_id: int
    values : list[ValueBase]
    class Config:
        orm_mode = True


class VarValue(BaseModel):
    tag_id: int
    value: str

class ValueForPoints(BaseModel):
    org_id: int
    points: list[int]
    date_from: str
    date_to: str
    skip: int
    limit: int
