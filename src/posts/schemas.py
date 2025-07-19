from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    content: str
    author: str


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class PostInDB(PostBase):
    id: int

    class Config:
        from_attributes = True
