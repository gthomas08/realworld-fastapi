"""Comment schema definitions."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator

from src.profiles.schemas import ProfileResponse


class NewComment(BaseModel):
    """Schema for creating a new comment."""
    body: str = Field(..., min_length=1)

    @field_validator('body')
    @classmethod
    def validate_body(cls, v):
        if not v.strip():
            raise ValueError('Comment body cannot be empty')
        return v.strip()


class Comment(BaseModel):
    """Comment response schema."""
    id: int
    createdAt: datetime = Field(alias="createdAt")
    updatedAt: datetime = Field(alias="updatedAt")
    body: str
    author: ProfileResponse

    model_config = {"from_attributes": True, "populate_by_name": True}


class NewCommentRequest(BaseModel):
    """Request schema for creating a new comment."""
    comment: NewComment


class SingleCommentResponse(BaseModel):
    """Response schema for a single comment."""
    comment: Comment


class MultipleCommentsResponse(BaseModel):
    """Response schema for multiple comments."""
    comments: List[Comment]
