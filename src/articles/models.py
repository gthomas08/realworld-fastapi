from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID
import uuid

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from src.database import Base

if TYPE_CHECKING:
    from src.users.models import User
    from src.tags.models import Tag

# Association table for article tags (many-to-many)
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', PostgreSQLUUID(as_uuid=True), ForeignKey(
        'articles.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey(
        'tags.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for article favorites (many-to-many)
article_favorites = Table(
    'article_favorites',
    Base.metadata,
    Column('article_id', PostgreSQLUUID(as_uuid=True), ForeignKey(
        'articles.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', PostgreSQLUUID(as_uuid=True), ForeignKey(
        'users.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime(timezone=True),
           server_default=func.now(), nullable=False)
)


class Article(Base):
    """Article model for blog posts."""

    __tablename__ = 'articles'

    id: Mapped[UUID] = Column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    slug: Mapped[str] = Column(
        String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)
    body: Mapped[str] = Column(Text, nullable=False)
    author_id: Mapped[UUID] = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    favorites_count: Mapped[int] = Column(
        Integer, nullable=False, default=0, index=True)
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
        nullable=False,
        index=True
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User", back_populates="articles", lazy="selectin")
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=article_tags,
        back_populates="articles",
        lazy="selectin"
    )
    favorited_by: Mapped[List["User"]] = relationship(
        "User",
        secondary=article_favorites,
        back_populates="favorite_articles",
        lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, slug='{self.slug}', title='{self.title}')>"

    @property
    def tag_list(self) -> List[str]:
        """Get list of tag names."""
        return [tag.name for tag in self.tags]

    def is_favorited_by(self, user_id: Optional[UUID]) -> bool:
        """Check if article is favorited by specific user."""
        if not user_id:
            return False
        return any(user.id == user_id for user in self.favorited_by)
