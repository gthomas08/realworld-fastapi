from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from .service import TagService
from .schemas import TagsResponse

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=TagsResponse)
async def get_tags(
    session: AsyncSession = Depends(get_async_session)
):
    """Get all tags."""
    service = TagService(session)
    tags = await service.get_all_tags()
    return TagsResponse(tags=tags)
