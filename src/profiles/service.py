from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, exists
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.users.models import User, user_follows


class ProfileService:
    """Service class for profile operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_profile_by_username(
        self, username: str, current_user: Optional[User] = None
    ) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None
        if current_user:
            user.is_following = await self._is_following(current_user.id, user.id)
        else:
            user.is_following = False
        return user

    async def follow_user(self, follower: User, username: str) -> User:
        user_to_follow = await self._get_user_by_username(username)
        if not user_to_follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        if user_to_follow.id == follower.id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot follow yourself",
            )
        is_following = await self._is_following(follower.id, user_to_follow.id)
        if is_following:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Already following this user",
            )
        follow_stmt = user_follows.insert().values(
            follower_id=follower.id, followed_id=user_to_follow.id
        )
        await self.session.execute(follow_stmt)
        await self.session.commit()
        await self.session.refresh(user_to_follow)
        user_to_follow.is_following = True
        return user_to_follow

    async def unfollow_user(self, follower: User, username: str) -> User:
        user_to_unfollow = await self._get_user_by_username(username)
        if not user_to_unfollow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        is_following = await self._is_following(follower.id, user_to_unfollow.id)
        if not is_following:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Not following this user",
            )
        delete_stmt = user_follows.delete().where(
            and_(
                user_follows.c.follower_id == follower.id,
                user_follows.c.followed_id == user_to_unfollow.id,
            )
        )
        await self.session.execute(delete_stmt)
        await self.session.commit()
        await self.session.refresh(user_to_unfollow)
        user_to_unfollow.is_following = False
        return user_to_unfollow

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _is_following(self, follower_id: str, followed_id: str) -> bool:
        stmt = select(
            exists().where(
                and_(
                    user_follows.c.follower_id == follower_id,
                    user_follows.c.followed_id == followed_id,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar()
