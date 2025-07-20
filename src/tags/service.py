from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import Tag


class TagService:
    """Service class for tag operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_tags(self) -> List[str]:
        """Get all tag names."""
        stmt = select(Tag.name).order_by(Tag.name)
        result = await self.session.execute(stmt)
        return [tag_name for tag_name in result.scalars().all()]
