from pydantic import BaseModel

class OrgEntityPermissionBase(BaseModel):
    entity_id : int


class OrgEntityPermissionCreate(OrgEntityPermissionBase):
    org_name : str
    class Config:
        orm_mode = True

class OrgEntityPermission(OrgEntityPermissionBase):
    id: int
    org_id : int
    class Config:
        orm_mode = True