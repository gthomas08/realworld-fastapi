from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from .models import Article, Comment, article_favorites, article_tags
from src.users.models import User, user_follows
from src.tags.models import Tag
from src.profiles.service import ProfileService


def slugify(title: str) -> str:
    """Convert title to URL-friendly slug."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


class ArticleService:
    """Service class for article operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_service = ProfileService(session)

    async def get_articles(
        self,
        current_user: Optional[User] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Article], int]:
        """Get articles with filtering, pagination, and user context."""

        # Build the base query
        query = select(Article).options(
            selectinload(Article.author),
            selectinload(Article.tags),
            selectinload(Article.favorited_by)
        )

        # Count query for total articles
        count_query = select(func.count(Article.id))

        # Apply filters
        filters = []

        if tag:
            # Filter by tag
            tag_subquery = select(article_tags.c.article_id).join(
                Tag).where(Tag.name == tag.lower())
            filters.append(Article.id.in_(tag_subquery))

        if author:
            # Filter by author username
            author_subquery = select(User.id).where(User.username == author)
            filters.append(Article.author_id.in_(author_subquery))

        if favorited:
            # Filter by user who favorited
            user_subquery = select(User.id).where(User.username == favorited)
            favorited_subquery = select(article_favorites.c.article_id).where(
                article_favorites.c.user_id.in_(user_subquery)
            )
            filters.append(Article.id.in_(favorited_subquery))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Order by creation date (most recent first)
        query = query.order_by(desc(Article.created_at))

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute queries
        result = await self.session.execute(query)
        articles = result.scalars().all()

        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()

        # Set favorited status and following status for current user
        if current_user:
            for article in articles:
                article.favorited = article.is_favorited_by(current_user.id)
                # Set is_following attribute on the author
                article.author.is_following = await self.profile_service._is_following(
                    current_user.id, article.author.id
                )
                # Pre-compute tag list to avoid lazy loading in router
                article._tag_list = [tag.name for tag in article.tags] if hasattr(
                    article, 'tags') else []
        else:
            for article in articles:
                article.favorited = False
                article.author.is_following = False
                # Pre-compute tag list to avoid lazy loading in router
                article._tag_list = [tag.name for tag in article.tags] if hasattr(
                    article, 'tags') else []

        return list(articles), total_count

    async def get_feed(
        self,
        current_user: User,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Article], int]:
        """Get feed of articles from followed users."""

        # Get followed user IDs
        followed_users_query = select(user_follows.c.followed_id).where(
            user_follows.c.follower_id == current_user.id
        )

        # Build main query for articles from followed users
        query = select(Article).options(
            selectinload(Article.author),
            selectinload(Article.tags),
            selectinload(Article.favorited_by)
        ).where(
            Article.author_id.in_(followed_users_query)
        ).order_by(desc(Article.created_at))

        # Count query
        count_query = select(func.count(Article.id)).where(
            Article.author_id.in_(followed_users_query)
        )

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute queries
        result = await self.session.execute(query)
        articles = result.scalars().all()

        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()

        # Set favorited status and following status for current user
        for article in articles:
            article.favorited = article.is_favorited_by(current_user.id)
            # Since this is a feed of followed users, they are all following
            article.author.is_following = True
            # Pre-compute tag list to avoid lazy loading in router
            article._tag_list = [tag.name for tag in article.tags] if hasattr(
                article, 'tags') else []

        return list(articles), total_count

    async def get_article_by_slug(
        self,
        slug: str,
        current_user: Optional[User] = None
    ) -> Optional[Article]:
        """Get article by slug with user context."""

        query = select(Article).options(
            selectinload(Article.author),
            selectinload(Article.tags),
            selectinload(Article.favorited_by)
        ).where(Article.slug == slug)

        result = await self.session.execute(query)
        article = result.scalar_one_or_none()

        if article:
            # Set favorited status and following status
            if current_user:
                article.favorited = article.is_favorited_by(current_user.id)
                article.author.is_following = await self.profile_service._is_following(
                    current_user.id, article.author.id
                )
            else:
                article.favorited = False
                article.author.is_following = False
            # Pre-compute tag list to avoid lazy loading in router
            article._tag_list = [tag.name for tag in article.tags] if hasattr(
                article, 'tags') else []

        return article

    async def create_article(
        self,
        author: User,
        title: str,
        description: str,
        body: str,
        tag_list: List[str]
    ) -> Article:
        """Create a new article."""

        # Generate unique slug
        base_slug = slugify(title)
        slug = base_slug
        counter = 1

        while await self._slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Create article
        article = Article(
            slug=slug,
            title=title,
            description=description,
            body=body,
            author_id=author.id
        )

        self.session.add(article)
        await self.session.flush()  # Get the article ID

        # Handle tags
        if tag_list:
            await self._process_article_tags(article, tag_list)

        await self.session.commit()
        await self.session.refresh(article)

        # Manually set author to avoid relationship loading issues
        if not article.author:
            article.author = author

        # Set favorited status (false for new articles) and following status (false for own articles)
        article.favorited = False
        article.author.is_following = False
        # Pre-compute tag list to avoid lazy loading in router
        article._tag_list = tag_list

        return article

    async def update_article(
        self,
        slug: str,
        current_user: User,
        title: Optional[str] = None,
        description: Optional[str] = None,
        body: Optional[str] = None
    ) -> Article:
        """Update an article."""

        article = await self.get_article_by_slug(slug, current_user)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Check authorization
        if article.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own articles"
            )

        # Update fields
        updated = False

        if title is not None and title != article.title:
            # Generate new slug if title changed
            base_slug = slugify(title)
            new_slug = base_slug
            counter = 1

            # Ensure new slug is unique and different from current
            while await self._slug_exists(new_slug) and new_slug != article.slug:
                new_slug = f"{base_slug}-{counter}"
                counter += 1

            article.title = title
            article.slug = new_slug
            updated = True

        if description is not None and description != article.description:
            article.description = description
            updated = True

        if body is not None and body != article.body:
            article.body = body
            updated = True

        if updated:
            article.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(article, ['author', 'tags'])

        # Set favorited status and following status (false for own articles)
        article.favorited = article.is_favorited_by(current_user.id)
        article.author.is_following = False
        # Pre-compute tag list to avoid lazy loading in router
        article._tag_list = [tag.name for tag in article.tags] if hasattr(
            article, 'tags') else []

        return article

    async def delete_article(self, slug: str, current_user: User) -> bool:
        """Delete an article."""

        article = await self.get_article_by_slug(slug)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Check authorization
        if article.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own articles"
            )

        await self.session.delete(article)
        await self.session.commit()
        return True

    async def favorite_article(self, slug: str, current_user: User) -> Article:
        """Favorite an article."""

        article = await self.get_article_by_slug(slug, current_user)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Check if already favorited
        if article.is_favorited_by(current_user.id):
            article.favorited = True
            # Set following status
            article.author.is_following = await self.profile_service._is_following(
                current_user.id, article.author.id
            )
            # Pre-compute tag list to avoid lazy loading in router
            article._tag_list = [tag.name for tag in article.tags] if hasattr(
                article, 'tags') else []
            return article

        # Store attributes before modification to avoid lazy loading after commit
        article_id = article.id

        # Add to favorites
        article.favorited_by.append(current_user)
        article.favorites_count += 1

        await self.session.commit()

        # Re-fetch article with all relationships to avoid lazy loading
        query = select(Article).options(
            selectinload(Article.author),
            selectinload(Article.tags),
            selectinload(Article.favorited_by)
        ).where(Article.id == article_id)
        result = await self.session.execute(query)
        article = result.scalar_one()

        article.favorited = True
        # Set following status
        article.author.is_following = await self.profile_service._is_following(
            current_user.id, article.author.id
        )
        # Pre-compute tag list to avoid lazy loading in router
        article._tag_list = [
            tag.name for tag in article.tags] if article.tags else []
        return article

    async def unfavorite_article(self, slug: str, current_user: User) -> Article:
        """Unfavorite an article."""

        article = await self.get_article_by_slug(slug, current_user)
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found"
            )

        # Check if not favorited
        if not article.is_favorited_by(current_user.id):
            article.favorited = False
            # Set following status
            article.author.is_following = await self.profile_service._is_following(
                current_user.id, article.author.id
            )
            # Pre-compute tag list to avoid lazy loading in router
            article._tag_list = [tag.name for tag in article.tags] if hasattr(
                article, 'tags') else []
            return article

        # Store attributes before modification to avoid lazy loading after commit
        article_id = article.id

        # Remove from favorites
        article.favorited_by.remove(current_user)
        article.favorites_count = max(0, article.favorites_count - 1)

        await self.session.commit()

        # Re-fetch article with all relationships to avoid lazy loading
        query = select(Article).options(
            selectinload(Article.author),
            selectinload(Article.tags),
            selectinload(Article.favorited_by)
        ).where(Article.id == article_id)
        result = await self.session.execute(query)
        article = result.scalar_one()

        article.favorited = False
        # Set following status
        article.author.is_following = await self.profile_service._is_following(
            current_user.id, article.author.id
        )
        # Pre-compute tag list to avoid lazy loading in router
        article._tag_list = [
            tag.name for tag in article.tags] if article.tags else []
        return article

    async def _slug_exists(self, slug: str) -> bool:
        """Check if slug already exists."""
        query = select(Article.id).where(Article.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def _process_article_tags(self, article: Article, tag_names: List[str]) -> None:
        """Process and associate tags with article."""
        # Get existing article tags to avoid lazy loading
        existing_tags_query = select(Tag).join(article_tags).where(
            article_tags.c.article_id == article.id)
        existing_tags_result = await self.session.execute(existing_tags_query)
        existing_tags = {
            tag.name: tag for tag in existing_tags_result.scalars().all()}

        for tag_name in tag_names:
            tag_name_lower = tag_name.lower()

            # Skip if tag is already associated
            if tag_name_lower in existing_tags:
                continue

            # Get or create tag
            tag_query = select(Tag).where(Tag.name == tag_name_lower)
            result = await self.session.execute(tag_query)
            tag = result.scalar_one_or_none()

            if not tag:
                tag = Tag(name=tag_name_lower)
                self.session.add(tag)
                await self.session.flush()

            # Associate with article using direct SQL to avoid lazy loading
            from sqlalchemy import insert
            insert_stmt = insert(article_tags).values(
                article_id=article.id,
                tag_id=tag.id
            )
            await self.session.execute(insert_stmt)


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
        await self.session.refresh(comment, ['author'])

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
