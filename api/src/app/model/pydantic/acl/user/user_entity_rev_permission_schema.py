from pydantic import BaseModel

class UserEntityRevPermissionsBase(BaseModel):
    entity_id : int


class UserEntityRevPermissionsRelationCreate(UserEntityRevPermissionsBase):
    class Config:
        orm_mode = True

class UserEntityRevPermissionsCreate(UserEntityRevPermissionsRelationCreate):
    org_id : int
    user_email : str
    class Config:
        orm_mode = True

class UserEntityRevPermissions(UserEntityRevPermissionsBase):
    id: int
    user_id : int
    class Config:
        orm_mode = True

class UserEntityRevPermissionsDelete(BaseModel):
    org_id : int