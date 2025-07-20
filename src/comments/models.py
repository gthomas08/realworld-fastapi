"""Comment model definition."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from src.database import Base

if TYPE_CHECKING:
    from src.users.models import User
    from src.articles.models import Article


class Comment(Base):
    """Comment model for article comments."""

    __tablename__ = 'comments'

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    body: Mapped[str] = Column(Text, nullable=False)
    article_id: Mapped[UUID] = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey('articles.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    author_id: Mapped[UUID] = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    article: Mapped["Article"] = relationship("Article")
    author: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, article_id={self.article_id}, author_id={self.author_id})>"
