from pydantic import BaseModel
from app.model.pydantic.acl.user import user_entity_add_permission_schema, \
    user_tag_rev_permission_schema, \
    user_tag_add_permission_schema, \
    user_entity_rev_permission_schema
from typing import Optional


class UserBase(BaseModel):
    email : str

class UserShort(BaseModel):
    id: int
class UserCreate(UserBase):
    org_id : int
    visible_entities : Optional[list[user_entity_add_permission_schema.UserEntityAddPermissionsRelationCreate]]
    invisible_entities : Optional[list[user_entity_rev_permission_schema.UserEntityRevPermissionsRelationCreate]]
    visible_tags : Optional[list[user_tag_add_permission_schema.UserTagAddPermissionsRelationCreate]]
    invisible_tags : Optional[list[user_tag_rev_permission_schema.UserTagRevPermissionsRelationCreate]]
    class Config:
        orm_mode = True

class User(UserShort):
    id: int
    visible_entities: Optional[list[user_entity_add_permission_schema.UserEntityAddPermissions]]
    invisible_entities: Optional[list[user_entity_rev_permission_schema.UserEntityRevPermissions]]
    visible_tags: Optional[list[user_tag_add_permission_schema.UserTagAddPermissions]]
    invisible_tags: Optional[list[user_tag_rev_permission_schema.UserTagRevPermissions]]
    class Config:
        orm_mode = True

class UserDelete(BaseModel):
    org_id : int