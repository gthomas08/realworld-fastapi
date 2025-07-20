from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re


class ProfileSchema(BaseModel):
    """Profile schema for embedded author information."""
    username: str
    bio: str
    image: str
    following: bool


class NewArticle(BaseModel):
    """Schema for creating a new article."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    tagList: Optional[List[str]] = Field(default_factory=list, alias="tagList")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

    @field_validator('body')
    @classmethod
    def validate_body(cls, v):
        if not v.strip():
            raise ValueError('Body cannot be empty')
        return v.strip()

    @field_validator('tagList')
    @classmethod
    def validate_tag_list(cls, v):
        if v is None:
            return []
        # Normalize tags and remove duplicates
        normalized_tags = []
        for tag in v:
            if tag and tag.strip():
                # Normalize tag: lowercase, replace spaces with hyphens
                normalized_tag = re.sub(r'\s+', '-', tag.strip().lower())
                if normalized_tag not in normalized_tags:
                    normalized_tags.append(normalized_tag)
        return normalized_tags


class UpdateArticle(BaseModel):
    """Schema for updating an article."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    body: Optional[str] = Field(None, min_length=1)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip() if v else v

    @field_validator('body')
    @classmethod
    def validate_body(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Body cannot be empty')
        return v.strip() if v else v


class Article(BaseModel):
    """Article response schema."""
    slug: str
    title: str
    description: str
    body: str
    tagList: List[str] = Field(alias="tagList")
    createdAt: datetime = Field(alias="createdAt")
    updatedAt: datetime = Field(alias="updatedAt")
    favorited: bool
    favoritesCount: int = Field(alias="favoritesCount")
    author: ProfileSchema

    model_config = {"from_attributes": True, "populate_by_name": True}


class NewArticleRequest(BaseModel):
    """Request schema for creating a new article."""
    article: NewArticle


class UpdateArticleRequest(BaseModel):
    """Request schema for updating an article."""
    article: UpdateArticle


class SingleArticleResponse(BaseModel):
    """Response schema for a single article."""
    article: Article


class MultipleArticlesResponse(BaseModel):
    """Response schema for multiple articles."""
    articles: List[Article]
    articlesCount: int = Field(alias="articlesCount")

    model_config = {"populate_by_name": True}


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
    author: ProfileSchema

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
