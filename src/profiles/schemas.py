from typing import Optional
from datetime import datetime
import uuid
import re

from pydantic import BaseModel, Field, validator


class ProfileResponse(BaseModel):
    """Profile response schema for public profile data."""
    username: str = Field(..., description="Username of the profile")
    bio: str = Field(default="", description="Short bio of the user")
    image: str = Field(default="", description="Profile image URL")
    following: bool = Field(...,
                            description="Whether current user follows this profile")

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    username: Optional[str] = Field(
        None, min_length=3, max_length=255, description="New username")
    bio: Optional[str] = Field(None, max_length=1000, description="New bio")
    image: Optional[str] = Field(
        None, max_length=500, description="New profile image URL")

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is None:
            return v

        # Username should contain only alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'Username can only contain letters, numbers, underscores, and hyphens')

        # Username cannot start or end with underscore or hyphen
        if v.startswith(('_', '-')) or v.endswith(('_', '-')):
            raise ValueError(
                'Username cannot start or end with underscore or hyphen')

        return v.lower()  # Store usernames in lowercase


class FollowResponse(BaseModel):
    """Response schema for follow/unfollow operations."""
    profile: ProfileResponse

    class Config:
        from_attributes = True


class ProfilesResponse(BaseModel):
    """Response schema for multiple profiles."""
    profiles: list[ProfileResponse]
    profiles_count: int

    class Config:
        from_attributes = True
