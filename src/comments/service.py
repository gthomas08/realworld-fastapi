"""Comment service for business logic operations."""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from src.users.models import User
from src.articles.models import Article
from src.profiles.service import ProfileService
from .models import Comment


class CommentService:
    """Service class for comment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_service = ProfileService(session)

    async def get_comments_for_article(
        self,
        slug: str,
        current_user: Optional[User] = None
    ) -> List[Comment]:
        """Get all comments for an article."""

        # First verify article exists
        article_query = select(Article.id).where(Article.slug == slug)
        result = await self.session.execute(article_query)
        article_id = result.scalar_one_or_none()

        if not article_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Get comments
        query = select(Comment).options(
            selectinload(Comment.author)
        ).where(
            Comment.article_id == article_id
        ).order_by(desc(Comment.created_at))

        result = await self.session.execute(query)
        comments = result.scalars().all()

        # Set following status for current user
        if current_user:
            for comment in comments:
                comment.author.is_following = await self.profile_service._is_following(
                    current_user.id, comment.author.id
                )
        else:
            for comment in comments:
                comment.author.is_following = False

        return list(comments)

    async def create_comment(
        self,
        slug: str,
        author: User,
        body: str
    ) -> Comment:
        """Create a new comment on an article."""

        # Get article
        article_query = select(Article.id).where(Article.slug == slug)
        result = await self.session.execute(article_query)
        article_id = result.scalar_one_or_none()

        if not article_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Create comment
        comment = Comment(
            body=body,
            article_id=article_id,
            author_id=author.id
        )

        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)

        # Ensure author relationship is loaded
        if not comment.author:
            # Manually fetch author if not loaded
            author_query = select(User).where(User.id == comment.author_id)
            result = await self.session.execute(author_query)
            comment.author = result.scalar_one()

        # Set following status (false for own comments)
        comment.author.is_following = False

        return comment

    async def delete_comment(
        self,
        slug: str,
        comment_id: int,
        current_user: User
    ) -> bool:
        """Delete a comment."""

        # Verify article exists
        article_query = select(Article.id).where(Article.slug == slug)
        result = await self.session.execute(article_query)
        article_id = result.scalar_one_or_none()

        if not article_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Get comment
        comment_query = select(Comment).where(
            and_(Comment.id == comment_id, Comment.article_id == article_id)
        )
        result = await self.session.execute(comment_query)
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        # Check authorization
        if comment.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments"
            )

        await self.session.delete(comment)
        await self.session.commit()
        return True
