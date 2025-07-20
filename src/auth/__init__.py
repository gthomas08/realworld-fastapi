"""Authentication module for Real World FastAPI."""

from .backend import auth_backend, get_jwt_strategy
from .dependencies import current_active_user, current_superuser, fastapi_users
from .manager import UserManager, get_user_db, get_user_manager
from .router import auth_router
from .schemas import UserCreate, UserRead, UserUpdate

__all__ = [
    "auth_backend",
    "get_jwt_strategy",
    "current_active_user",
    "current_superuser",
    "fastapi_users",
    "UserManager",
    "get_user_db",
    "get_user_manager",
    "auth_router",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
