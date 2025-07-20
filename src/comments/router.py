"""Comment router for handling comment-related endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.auth.dependencies import current_active_user, current_user_optional
from src.users.models import User
from src.profiles.schemas import ProfileResponse
from .service import CommentService
from .schemas import (
    NewCommentRequest,
    SingleCommentResponse,
    MultipleCommentsResponse,
    Comment as CommentSchema
)

router = APIRouter(prefix="/articles", tags=["comments"])


def _user_to_profile_schema(user: User, is_following: bool = False) -> ProfileResponse:
    """Convert User model to ProfileResponse."""
    return ProfileResponse(
        username=user.username,
        bio=user.bio or "",
        image=user.image or "",
        following=is_following
    )


def _comment_to_schema(comment, current_user: Optional[User] = None) -> CommentSchema:
    """Convert Comment model to CommentSchema."""
    # Check if the author has the is_following attribute set by the service
    is_following = getattr(comment.author, 'is_following', False)

    return CommentSchema(
        id=comment.id,
        createdAt=comment.created_at,
        updatedAt=comment.updated_at,
        body=comment.body,
        author=_user_to_profile_schema(comment.author, is_following)
    )


@router.get("/{slug}/comments", response_model=MultipleCommentsResponse)
async def get_article_comments(
    slug: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(current_user_optional)
):
    """
    Get comments for an article.

    Returns all comments for the specified article.
    Authentication is optional.
    """
    service = CommentService(session)
    comments = await service.get_comments_for_article(slug, current_user)

    comment_schemas = [_comment_to_schema(
        comment, current_user) for comment in comments]

    return MultipleCommentsResponse(comments=comment_schemas)


@router.post("/{slug}/comments", response_model=SingleCommentResponse)
async def create_article_comment(
    slug: str,
    comment_data: NewCommentRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Create a comment for an article.

    Adds a new comment to the specified article.
    Authentication is required.
    """
    service = CommentService(session)
    comment = await service.create_comment(
        slug=slug,
        author=current_user,
        body=comment_data.comment.body
    )

    comment_schema = _comment_to_schema(comment, current_user)

    return SingleCommentResponse(comment=comment_schema)


@router.delete("/{slug}/comments/{id}", status_code=status.HTTP_200_OK)
async def delete_article_comment(
    slug: str,
    id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Delete a comment for an article.

    Deletes a comment from the specified article.
    Only the comment author can delete it.
    Authentication is required.
    """
    service = CommentService(session)
    await service.delete_comment(slug, id, current_user)

    return {}
