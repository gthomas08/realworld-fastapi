from typing import Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    """Profile response schema for public profile data."""
    username: str = Field(..., description="Username of the profile")
    bio: str = Field(default="", description="Short bio of the user")
    image: str = Field(default="", description="Profile image URL")
    following: bool = Field(...,
                            description="Whether current user follows this profile")

    class Config:
        from_attributes = True


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
