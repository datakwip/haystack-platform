from pydantic import BaseModel
from typing import Optional
from app.model.pydantic.acl.user.user_schema import User
from app.model.pydantic.acl.org.org_schema import Org

class OrgUser(BaseModel):
    user : User
    org :   Org

    class Config:
        orm_mode = True