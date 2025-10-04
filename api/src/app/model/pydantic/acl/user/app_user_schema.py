from pydantic import BaseModel
from app.model.pydantic.acl.user import user_schema


class AppUserCreate(BaseModel):
    user_email : str
    class Config:
        orm_mode = True

class AppUser(BaseModel):
    id: int
    user : user_schema.User
    class Config:
        orm_mode = True
