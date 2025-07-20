from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.auth.dependencies import current_active_user, current_user_optional
from src.users.models import User
from .service import ProfileService
from .schemas import ProfileResponse, FollowResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _user_to_profile_response(user: User, is_following: bool = False) -> ProfileResponse:
    """Convert User model to ProfileResponse."""
    return ProfileResponse(
        username=user.username,
        bio=user.bio,
        image=user.image,
        following=is_following
    )


@router.get("/{username}", response_model=ProfileResponse)
async def get_profile(
    username: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(current_user_optional)
):
    """Get user profile by username. Authentication is optional."""
    profile_service = ProfileService(session)
    user = await profile_service.get_profile_by_username(username, current_user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Get following status if user is authenticated
    is_following = getattr(user, 'is_following', False)

    return _user_to_profile_response(user, is_following)


@router.post("/{username}/follow", response_model=FollowResponse)
async def follow_profile(
    username: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Follow a user profile."""
    profile_service = ProfileService(session)
    followed_user = await profile_service.follow_user(current_user, username)

    profile_response = _user_to_profile_response(followed_user, True)
    return FollowResponse(profile=profile_response)


@router.delete("/{username}/follow", response_model=FollowResponse)
async def unfollow_profile(
    username: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Unfollow a user profile."""
    profile_service = ProfileService(session)
    unfollowed_user = await profile_service.unfollow_user(current_user, username)

    profile_response = _user_to_profile_response(unfollowed_user, False)
    return FollowResponse(profile=profile_response)
