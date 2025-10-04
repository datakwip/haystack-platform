from pydantic import BaseModel
from app.model.pydantic.source_objects import entity_tag_schema


class EntityBase(BaseModel):
    tags: list[entity_tag_schema.EntityTag]


class EntityCreate(EntityBase):
    org_id : int
    tags: list[entity_tag_schema.EntityTagCreate]
    class Config:
        orm_mode = True

class Entity(EntityBase):
    id: int
    tags: list[entity_tag_schema.EntityTag]
    class Config:
        orm_mode = True

class EntityDelete(BaseModel):
    org_id : int