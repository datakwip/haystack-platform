from pydantic import BaseModel

class UserTagAddPermissionsRelationCreate(BaseModel):
    tag_name : str
    class Config:
        orm_mode = True

class UserTagAddPermissionsCreate(UserTagAddPermissionsRelationCreate):
    org_id : int
    user_email : str
    class Config:
        orm_mode = True

class UserTagAddPermissions(BaseModel):
    id: int
    tag_id : int
    user_id : int
    class Config:
        orm_mode = True

class UserTagAddPermissionsDelete(BaseModel):
    org_id : int