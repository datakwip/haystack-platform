from pydantic import BaseModel
from typing import Optional, Union

class TagMetaRelationCreate(BaseModel):
        attribute: str
        value: Optional[Union[list[str], str]]

class TagMetaCreate(TagMetaRelationCreate):
    tag_id : int
    org_id : int
    class Config:
        orm_mode = True


class TagMeta(BaseModel):
    id: int
    tag_id: int
    attribute: int
    value: Optional[int]
    class Config:
        orm_mode = True

class TagMetaUpdate(TagMetaRelationCreate):
    org_id : int

    class Config:
        orm_mode = True

class TagMetaDelete(BaseModel):
    org_id : int
