from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, exists
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.users.models import User, user_follows


class ProfileService:
    """Service class for profile operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_profile_by_username(
        self,
        username: str,
        current_user: Optional[User] = None
    ) -> Optional[User]:
        """Get user profile by username."""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Check if current user follows this profile
        if current_user:
            user.is_following = await self._is_following(current_user.id, user.id)
        else:
            user.is_following = False

        return user

    async def update_profile(
        self,
        user: User,
        username: Optional[str] = None,
        bio: Optional[str] = None,
        image: Optional[str] = None
    ) -> User:
        """Update user profile."""
        try:
            if username is not None:
                # Check if username is already taken
                existing_user = await self._get_user_by_username(username)
                if existing_user and existing_user.id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Username already taken"
                    )
                user.username = username

            if bio is not None:
                user.bio = bio

            if image is not None:
                user.image = image

            await self.session.commit()
            await self.session.refresh(user)
            return user

        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username already taken"
            )

    async def follow_user(self, follower: User, username: str) -> User:
        """Follow a user by username."""
        # Get the user to follow
        user_to_follow = await self._get_user_by_username(username)
        if not user_to_follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        if user_to_follow.id == follower.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot follow yourself"
            )

        # Check if already following
        is_following = await self._is_following(follower.id, user_to_follow.id)
        if is_following:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Already following this user"
            )

        # Add follow relationship
        follow_stmt = user_follows.insert().values(
            follower_id=follower.id,
            followed_id=user_to_follow.id
        )
        await self.session.execute(follow_stmt)
        await self.session.commit()

        # Refresh and return the followed user
        await self.session.refresh(user_to_follow)
        user_to_follow.is_following = True
        return user_to_follow

    async def unfollow_user(self, follower: User, username: str) -> User:
        """Unfollow a user by username."""
        # Get the user to unfollow
        user_to_unfollow = await self._get_user_by_username(username)
        if not user_to_unfollow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        # Check if currently following
        is_following = await self._is_following(follower.id, user_to_unfollow.id)
        if not is_following:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Not following this user"
            )

        # Remove follow relationship
        delete_stmt = user_follows.delete().where(
            and_(
                user_follows.c.follower_id == follower.id,
                user_follows.c.followed_id == user_to_unfollow.id
            )
        )
        await self.session.execute(delete_stmt)
        await self.session.commit()

        # Refresh and return the unfollowed user
        await self.session.refresh(user_to_unfollow)
        user_to_unfollow.is_following = False
        return user_to_unfollow

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _is_following(self, follower_id: str, followed_id: str) -> bool:
        """Check if follower_id follows followed_id."""
        stmt = select(
            exists().where(
                and_(
                    user_follows.c.follower_id == follower_id,
                    user_follows.c.followed_id == followed_id
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar()
