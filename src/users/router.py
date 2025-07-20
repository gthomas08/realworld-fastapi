from fastapi import APIRouter, Depends

from src.auth.dependencies import current_active_user, fastapi_users
from src.auth.schemas import UserRead, UserUpdate
from .models import User

# Create router for user management routes only
router = APIRouter()

# Include user management routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
