import uuid
from typing import Optional
from datetime import datetime

from fastapi_users import schemas
from pydantic import Field, validator
import re


class UserRead(schemas.BaseUser[uuid.UUID]):
    """User read schema with profile fields."""

    username: str
    bio: str
    image: str
    created_at: datetime
    updated_at: datetime


class UserCreate(schemas.BaseUserCreate):
    """User creation schema with required profile fields."""

    username: str = Field(
        ..., min_length=3, max_length=255, description="Username (3-255 characters)"
    )
    bio: Optional[str] = Field("", max_length=1000, description="User bio")
    image: Optional[str] = Field("", max_length=500, description="Profile image URL")

    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if not v:
            raise ValueError("Username is required")

        # Username should contain only alphanumeric characters, underscores, and hyphens
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )

        # Username cannot start or end with underscore or hyphen
        if v.startswith(("_", "-")) or v.endswith(("_", "-")):
            raise ValueError("Username cannot start or end with underscore or hyphen")

        return v.lower()  # Store usernames in lowercase


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema with optional profile fields."""

    username: Optional[str] = Field(
        None, min_length=3, max_length=255, description="Username (3-255 characters)"
    )
    bio: Optional[str] = Field(None, max_length=1000, description="User bio")
    image: Optional[str] = Field(None, max_length=500, description="Profile image URL")

    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if v is None:
            return v

        # Username should contain only alphanumeric characters, underscores, and hyphens
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )

        # Username cannot start or end with underscore or hyphen
        if v.startswith(("_", "-")) or v.endswith(("_", "-")):
            raise ValueError("Username cannot start or end with underscore or hyphen")

        return v.lower()  # Store usernames in lowercase
