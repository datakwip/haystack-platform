from pydantic import BaseModel
from typing import Optional
from app.model.pydantic.source_objects import tag_meta_schema
from app.model.pydantic.source_objects import tag_def_enum_schema

class TagDefBase(BaseModel):
    name: str
    url: Optional[str]
    doc: Optional[str]
    dis: Optional[str]
    file_ext: Optional[str]
    mime: Optional[str]
    version: Optional[str]
    min_val: Optional[int]
    max_val: Optional[int]
    base_uri: Optional[str]
    pref_unit: Optional[list]


class TagDef(TagDefBase):
    id: int
#    metas: list[tag_meta_schema.TagMeta]
#    enums : Optional[list[tag_def_enum_schema.TagDefEnum]]
    class Config:
        orm_mode = True

class TagDefCreate(TagDefBase):
    org_id : int
    metas: list[tag_meta_schema.TagMetaRelationCreate]
    enums: Optional[list[tag_def_enum_schema.TagDefEnumRelationCreate]]

class TagDefUpdate(TagDefBase):
    org_id : int

class TagDefDelete(BaseModel):
    org_id : int