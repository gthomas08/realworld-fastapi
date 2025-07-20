"""Comments module for handling all comment-related operations."""

from .router import router
from .schemas import (
    NewComment,
    Comment,
    NewCommentRequest,
    SingleCommentResponse,
    MultipleCommentsResponse
)
from .service import CommentService
from .models import Comment as CommentModel

__all__ = [
    "router",
    "NewComment",
    "Comment",
    "NewCommentRequest",
    "SingleCommentResponse",
    "MultipleCommentsResponse",
    "CommentService",
    "CommentModel"
]
