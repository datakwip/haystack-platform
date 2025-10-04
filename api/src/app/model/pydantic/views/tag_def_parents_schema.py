from pydantic import BaseModel


class TagDefParents(BaseModel):
        tag_id: int
        parent_ids: str

        class Config:
                orm_mode = True
