from typing import List
from pydantic import BaseModel


class TagsResponse(BaseModel):
    """Response model for tags list."""
    tags: List[str]
