import uuid

from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers

from .backend import auth_backend
from .manager import get_user_manager
from .schemas import UserCreate, UserRead, UserUpdate
from src.users.models import User

# Create FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Create router for authentication routes
auth_router = APIRouter()

# Include authentication routes
auth_router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["Auth"],
)

# Include registration routes
auth_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)

# Include password reset routes
auth_router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"],
)

# Include verification routes
auth_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["Auth"],
)

# Current user dependency
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
