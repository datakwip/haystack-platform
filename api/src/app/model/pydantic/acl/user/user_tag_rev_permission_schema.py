from pydantic import BaseModel

class UserTagRevPermissionsRelationCreate(BaseModel):
    tag_name : str
    class Config:
        orm_mode = True

class UserTagRevPermissionsCreate(UserTagRevPermissionsRelationCreate):
    org_id : int
    user_email : str
    class Config:
        orm_mode = True

class UserTagRevPermissions(BaseModel):
    id: int
    tag_id : int
    user_id : int
    class Config:
        orm_mode = True

class UserTagRevPermissionsDelete(BaseModel):
    org_id : int