from pydantic import BaseModel
from typing import Dict
from app.model.pydantic.filter import filter_schema


class RequestFilter(filter_schema.ReportFilterRequest):

    class Config:
        orm_mode = True


class ReportBase(BaseModel):
    message: str

    class Config:
        orm_mode = True
