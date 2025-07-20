from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.auth.dependencies import current_active_user, current_user_optional
from src.users.models import User
from src.profiles.schemas import ProfileResponse
from .service import ArticleService
from .schemas import (
    NewArticleRequest,
    UpdateArticleRequest,
    SingleArticleResponse,
    MultipleArticlesResponse,
    Article as ArticleSchema,
    ProfileSchema
)

router = APIRouter(prefix="/articles", tags=["articles"])


def _user_to_profile_schema(user: User, is_following: bool = False) -> ProfileSchema:
    """Convert User model to ProfileSchema."""
    return ProfileSchema(
        username=user.username,
        bio=user.bio or "",
        image=user.image or "",
        following=is_following
    )


def _article_to_schema(article, current_user: Optional[User] = None) -> ArticleSchema:
    """Convert Article model to ArticleSchema."""
    # Check if the author has the is_following attribute set by the service
    is_following = getattr(article.author, 'is_following', False)

    # Safely get tag list - check if tags are loaded to avoid lazy loading
    try:
        tag_list = getattr(article, '_tag_list', None)
        if tag_list is None:
            # Fallback to accessing tags if they're already loaded
            if hasattr(article, '__dict__') and 'tags' in article.__dict__:
                tag_list = [tag.name for tag in article.tags]
            else:
                tag_list = []
    except:
        tag_list = []

    # Safely access attributes to avoid lazy loading
    try:
        slug = article.slug
        title = article.title
        description = article.description
        body = article.body
        created_at = article.created_at
        updated_at = article.updated_at
        favorites_count = article.favorites_count
    except:
        # If we can't access attributes due to expiration, use fallback values
        slug = getattr(article, 'slug', '')
        title = getattr(article, 'title', '')
        description = getattr(article, 'description', '')
        body = getattr(article, 'body', '')
        created_at = getattr(article, 'created_at', None)
        updated_at = getattr(article, 'updated_at', None)
        favorites_count = getattr(article, 'favorites_count', 0)

    return ArticleSchema(
        slug=slug,
        title=title,
        description=description,
        body=body,
        tagList=tag_list,
        createdAt=created_at,
        updatedAt=updated_at,
        favorited=getattr(article, 'favorited', False),
        favoritesCount=favorites_count,
        author=_user_to_profile_schema(article.author, is_following)
    )


@router.get("/feed", response_model=MultipleArticlesResponse)
async def get_articles_feed(
    limit: int = Query(default=20, ge=1, le=100,
                       description="Number of articles to return"),
    offset: int = Query(
        default=0, ge=0, description="Number of articles to skip"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Get recent articles from users you follow.

    Returns articles created by users that the current user follows,
    ordered by creation date (most recent first).
    Authentication is required.
    """
    service = ArticleService(session)
    articles, total_count = await service.get_feed(current_user, limit, offset)

    article_schemas = [_article_to_schema(
        article, current_user) for article in articles]

    return MultipleArticlesResponse(
        articles=article_schemas,
        articlesCount=total_count
    )


@router.get("", response_model=MultipleArticlesResponse)
async def get_articles(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    author: Optional[str] = Query(
        None, description="Filter by author (username)"),
    favorited: Optional[str] = Query(
        None, description="Filter by favorites of a user (username)"),
    limit: int = Query(default=20, ge=1, le=100,
                       description="Number of articles to return"),
    offset: int = Query(
        default=0, ge=0, description="Number of articles to skip"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(current_user_optional)
):
    """
    Get recent articles globally.

    Returns articles ordered by creation date (most recent first).
    Supports filtering by tag, author, and favorited user.
    Authentication is optional.
    """
    service = ArticleService(session)
    articles, total_count = await service.get_articles(
        current_user=current_user,
        tag=tag,
        author=author,
        favorited=favorited,
        limit=limit,
        offset=offset
    )

    article_schemas = [_article_to_schema(
        article, current_user) for article in articles]

    return MultipleArticlesResponse(
        articles=article_schemas,
        articlesCount=total_count
    )


@router.post("", response_model=SingleArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    article_data: NewArticleRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Create an article.

    Creates a new article with the authenticated user as the author.
    Authentication is required.
    """
    service = ArticleService(session)
    article = await service.create_article(
        author=current_user,
        title=article_data.article.title,
        description=article_data.article.description,
        body=article_data.article.body,
        tag_list=article_data.article.tagList
    )

    article_schema = _article_to_schema(article, current_user)

    return SingleArticleResponse(article=article_schema)


@router.get("/{slug}", response_model=SingleArticleResponse)
async def get_article(
    slug: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(current_user_optional)
):
    """
    Get an article by slug.

    Returns a single article identified by its slug.
    Authentication is optional.
    """
    service = ArticleService(session)
    article = await service.get_article_by_slug(slug, current_user)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    article_schema = _article_to_schema(article, current_user)

    return SingleArticleResponse(article=article_schema)


@router.put("/{slug}", response_model=SingleArticleResponse)
async def update_article(
    slug: str,
    article_data: UpdateArticleRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Update an article.

    Updates an existing article. Only the article author can update it.
    Authentication is required.
    """
    service = ArticleService(session)
    article = await service.update_article(
        slug=slug,
        current_user=current_user,
        title=article_data.article.title,
        description=article_data.article.description,
        body=article_data.article.body
    )

    article_schema = _article_to_schema(article, current_user)

    return SingleArticleResponse(article=article_schema)


@router.delete("/{slug}", status_code=status.HTTP_200_OK)
async def delete_article(
    slug: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Delete an article.

    Deletes an existing article. Only the article author can delete it.
    Authentication is required.
    """
    service = ArticleService(session)
    await service.delete_article(slug, current_user)

    return {}


@router.post("/{slug}/favorite", response_model=SingleArticleResponse)
async def favorite_article(
    slug: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Favorite an article.

    Adds the article to the current user's favorites.
    Authentication is required.
    """
    service = ArticleService(session)
    article = await service.favorite_article(slug, current_user)

    article_schema = _article_to_schema(article, current_user)

    return SingleArticleResponse(article=article_schema)


@router.delete("/{slug}/favorite", response_model=SingleArticleResponse)
async def unfavorite_article(
    slug: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """
    Unfavorite an article.

    Removes the article from the current user's favorites.
    Authentication is required.
    """
    service = ArticleService(session)
    article = await service.unfavorite_article(slug, current_user)

    article_schema = _article_to_schema(article, current_user)

    return SingleArticleResponse(article=article_schema)
