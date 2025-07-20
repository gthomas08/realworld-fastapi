from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, Text, DateTime, func, Table, ForeignKey, UUID, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from src.database import Base


# Association table for user follows relationship
user_follows = Table(
    "user_follows",
    Base.metadata,
    Column("follower_id", UUID, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True),
    Column("followed_id", UUID, ForeignKey(
        "users.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True),
           server_default=func.now(), nullable=False),
    CheckConstraint("follower_id != followed_id", name="no_self_follow")
)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model for authentication and profiles."""
    __tablename__ = "users"

    # Profile fields
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    image: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(
        timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    # Following relationships (users this user follows)
    following = relationship(
        "User",
        secondary=user_follows,
        primaryjoin="User.id == user_follows.c.follower_id",
        secondaryjoin="User.id == user_follows.c.followed_id",
        back_populates="followers"
    )

    # Followers relationships (users that follow this user)
    followers = relationship(
        "User",
        secondary=user_follows,
        primaryjoin="User.id == user_follows.c.followed_id",
        secondaryjoin="User.id == user_follows.c.follower_id",
        back_populates="following"
    )
