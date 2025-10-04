from pydantic import BaseModel

class OrgTagPermissionCreate(BaseModel):
    tag_name : str
    org_name : str
    class Config:
        orm_mode = True

class OrgTagPermission(BaseModel):
    id: int
    org_id : int
    tag_id : int
    class Config:
        orm_mode = True