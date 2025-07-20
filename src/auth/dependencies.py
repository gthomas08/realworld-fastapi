"""Authentication dependencies and utilities."""

from .router import current_active_user, current_superuser, fastapi_users

# Optional current user dependency (returns None if not authenticated)
current_user_optional = fastapi_users.current_user(optional=True)

__all__ = [
    "current_active_user",
    "current_superuser",
    "current_user_optional",
    "fastapi_users",
]
