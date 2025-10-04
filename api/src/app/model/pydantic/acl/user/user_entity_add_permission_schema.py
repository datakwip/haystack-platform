from pydantic import BaseModel

class UserEntityAddPermissionsBase(BaseModel):
    entity_id : int


class UserEntityAddPermissionsRelationCreate(UserEntityAddPermissionsBase):
    class Config:
        orm_mode = True

class UserEntityAddPermissionsCreate(UserEntityAddPermissionsRelationCreate):
    org_id : int
    user_email : str
    class Config:
        orm_mode = True

class UserEntityAddPermissions(UserEntityAddPermissionsBase):
    id: int
    user_id : int
    class Config:
        orm_mode = True

class UserEntityAddPermissionsDelete(BaseModel):
    org_id : int