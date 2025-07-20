import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from uuid import uuid4

from src.users.models import User
from src.articles.models import Article, Comment
from src.articles.service import ArticleService, CommentService
from src.articles.schemas import NewArticle, UpdateArticle, NewComment
from src.tags.models import Tag
from src.main import app
from src.database import Base


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_session():
    """Create an async session for testing."""
    # Create in-memory database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with AsyncSession(engine) as session:
        yield session

    # Clean up
    await engine.dispose()


class TestArticleSchemas:
    """Test article schema validation."""

    def test_new_article_schema(self):
        """Test NewArticle schema validation."""
        # Valid article
        article = NewArticle(
            title="Test Article",
            description="Test description",
            body="Test body content",
            tagList=["python", "testing"]
        )
        assert article.title == "Test Article"
        assert article.description == "Test description"
        assert article.body == "Test body content"
        assert article.tagList == ["python", "testing"]

    def test_new_article_tag_normalization(self):
        """Test tag normalization in NewArticle."""
        article = NewArticle(
            title="Test",
            description="Test",
            body="Test",
            tagList=["Python", "Machine Learning", "API Design"]
        )
        assert article.tagList == ["python", "machine-learning", "api-design"]

    def test_new_article_tag_deduplication(self):
        """Test tag deduplication in NewArticle."""
        article = NewArticle(
            title="Test",
            description="Test",
            body="Test",
            tagList=["python", "Python", "PYTHON", "react", "react"]
        )
        assert article.tagList == ["python", "react"]

    def test_update_article_schema(self):
        """Test UpdateArticle schema validation."""
        update = UpdateArticle(title="New Title")
        assert update.title == "New Title"
        assert update.description is None
        assert update.body is None

    def test_new_comment_schema(self):
        """Test NewComment schema validation."""
        comment = NewComment(body="This is a test comment")
        assert comment.body == "This is a test comment"


@pytest.mark.asyncio
class TestArticleService:
    """Test ArticleService methods."""

    @pytest_asyncio.fixture
    async def sample_user(self, async_session: AsyncSession):
        """Create a sample user for testing."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def another_user(self, async_session: AsyncSession):
        """Create another user for testing."""
        user = User(
            email="another@example.com",
            username="anotheruser",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def sample_article(self, async_session: AsyncSession, sample_user: User):
        """Create a sample article for testing."""
        service = ArticleService(async_session)
        article = await service.create_article(
            author=sample_user,
            title="Test Article",
            description="Test description",
            body="Test body content",
            tag_list=["python", "testing"]
        )
        return article

    @pytest.mark.asyncio
    async def test_create_article(self, async_session: AsyncSession, sample_user: User):
        """Test creating a new article."""
        service = ArticleService(async_session)

        article = await service.create_article(
            author=sample_user,
            title="Test Article",
            description="Test description",
            body="Test body content",
            tag_list=["python", "testing"]
        )

        assert article.title == "Test Article"
        assert article.description == "Test description"
        assert article.body == "Test body content"
        assert article.slug == "test-article"
        assert article.author_id == sample_user.id
        assert len(article.tags) == 2
        assert article.favorites_count == 0
        assert not article.favorited

    async def test_create_article_duplicate_slug(self, async_session: AsyncSession, sample_user: User):
        """Test creating articles with duplicate titles generates unique slugs."""
        service = ArticleService(async_session)

        # Create first article
        article1 = await service.create_article(
            author=sample_user,
            title="Test Article",
            description="Test description 1",
            body="Test body content 1",
            tag_list=[]
        )

        # Create second article with same title
        article2 = await service.create_article(
            author=sample_user,
            title="Test Article",
            description="Test description 2",
            body="Test body content 2",
            tag_list=[]
        )

        assert article1.slug == "test-article"
        assert article2.slug == "test-article-1"

    async def test_get_article_by_slug(self, async_session: AsyncSession, sample_article: Article, sample_user: User):
        """Test getting article by slug."""
        service = ArticleService(async_session)

        article = await service.get_article_by_slug(sample_article.slug, sample_user)

        assert article is not None
        assert article.id == sample_article.id
        assert article.slug == sample_article.slug
        assert not article.favorited  # User hasn't favorited it

    async def test_get_articles_with_pagination(self, async_session: AsyncSession, sample_user: User):
        """Test getting articles with pagination."""
        service = ArticleService(async_session)

        # Create multiple articles
        for i in range(5):
            await service.create_article(
                author=sample_user,
                title=f"Article {i}",
                description=f"Description {i}",
                body=f"Body {i}",
                tag_list=[]
            )

        # Test pagination
        articles, total_count = await service.get_articles(limit=3, offset=0)
        assert len(articles) == 3
        assert total_count == 5

        articles, total_count = await service.get_articles(limit=3, offset=3)
        assert len(articles) == 2
        assert total_count == 5

    async def test_get_articles_filter_by_tag(self, async_session: AsyncSession, sample_user: User):
        """Test filtering articles by tag."""
        service = ArticleService(async_session)

        # Create articles with different tags
        await service.create_article(
            author=sample_user,
            title="Python Article",
            description="About Python",
            body="Python content",
            tag_list=["python", "programming"]
        )

        await service.create_article(
            author=sample_user,
            title="JavaScript Article",
            description="About JavaScript",
            body="JavaScript content",
            tag_list=["javascript", "programming"]
        )

        # Filter by python tag
        articles, total_count = await service.get_articles(tag="python")
        assert len(articles) == 1
        assert articles[0].title == "Python Article"
        assert total_count == 1

    async def test_get_articles_filter_by_author(self, async_session: AsyncSession, sample_user: User, another_user: User):
        """Test filtering articles by author."""
        service = ArticleService(async_session)

        # Create articles by different authors
        await service.create_article(
            author=sample_user,
            title="Article by User 1",
            description="Description",
            body="Body",
            tag_list=[]
        )

        await service.create_article(
            author=another_user,
            title="Article by User 2",
            description="Description",
            body="Body",
            tag_list=[]
        )

        # Filter by author
        articles, total_count = await service.get_articles(author=sample_user.username)
        assert len(articles) == 1
        assert articles[0].title == "Article by User 1"
        assert total_count == 1

    async def test_update_article(self, async_session: AsyncSession, sample_article: Article, sample_user: User):
        """Test updating an article."""
        service = ArticleService(async_session)

        updated_article = await service.update_article(
            slug=sample_article.slug,
            current_user=sample_user,
            title="Updated Title",
            description="Updated description"
        )

        assert updated_article.title == "Updated Title"
        assert updated_article.description == "Updated description"
        assert updated_article.body == sample_article.body  # Unchanged
        assert updated_article.slug == "updated-title"  # Slug updated

    async def test_update_article_unauthorized(self, async_session: AsyncSession, sample_article: Article, another_user: User):
        """Test updating article by non-author raises error."""
        service = ArticleService(async_session)

        with pytest.raises(Exception):  # Should raise HTTPException
            await service.update_article(
                slug=sample_article.slug,
                current_user=another_user,
                title="Unauthorized Update"
            )

    async def test_delete_article(self, async_session: AsyncSession, sample_article: Article, sample_user: User):
        """Test deleting an article."""
        service = ArticleService(async_session)

        result = await service.delete_article(sample_article.slug, sample_user)
        assert result is True

        # Verify article is deleted
        deleted_article = await service.get_article_by_slug(sample_article.slug)
        assert deleted_article is None

    async def test_delete_article_unauthorized(self, async_session: AsyncSession, sample_article: Article, another_user: User):
        """Test deleting article by non-author raises error."""
        service = ArticleService(async_session)

        with pytest.raises(Exception):  # Should raise HTTPException
            await service.delete_article(sample_article.slug, another_user)

    async def test_favorite_article(self, async_session: AsyncSession, sample_article: Article, another_user: User):
        """Test favoriting an article."""
        service = ArticleService(async_session)

        favorited_article = await service.favorite_article(sample_article.slug, another_user)

        assert favorited_article.favorited is True
        assert favorited_article.favorites_count == 1

    async def test_unfavorite_article(self, async_session: AsyncSession, sample_article: Article, another_user: User):
        """Test unfavoriting an article."""
        service = ArticleService(async_session)

        # First favorite it
        await service.favorite_article(sample_article.slug, another_user)

        # Then unfavorite it
        unfavorited_article = await service.unfavorite_article(sample_article.slug, another_user)

        assert unfavorited_article.favorited is False
        assert unfavorited_article.favorites_count == 0

    async def test_get_feed(self, async_session: AsyncSession, sample_user: User, another_user: User):
        """Test getting user feed."""
        service = ArticleService(async_session)

        # Make sample_user follow another_user
        sample_user.following.append(another_user)
        await async_session.commit()

        # Create article by followed user
        await service.create_article(
            author=another_user,
            title="Feed Article",
            description="From followed user",
            body="Content",
            tag_list=[]
        )

        # Create article by non-followed user (should not appear in feed)
        unfollowed_user = User(
            email="unfollowed@example.com",
            username="unfollowed",
            hashed_password="password",
            is_active=True,
            is_verified=True
        )
        async_session.add(unfollowed_user)
        await async_session.commit()

        await service.create_article(
            author=unfollowed_user,
            title="Not in Feed",
            description="From unfollowed user",
            body="Content",
            tag_list=[]
        )

        # Get feed
        articles, total_count = await service.get_feed(sample_user)

        assert len(articles) == 1
        assert articles[0].title == "Feed Article"
        assert total_count == 1


@pytest.mark.asyncio
class TestCommentService:
    """Test CommentService methods."""

    @pytest_asyncio.fixture
    async def sample_user(self, async_session: AsyncSession):
        """Create a sample user for testing."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user

    @pytest_asyncio.fixture
    async def sample_article(self, async_session: AsyncSession, sample_user: User):
        """Create a sample article for testing."""
        article_service = ArticleService(async_session)
        article = await article_service.create_article(
            author=sample_user,
            title="Test Article",
            description="Test description",
            body="Test body content",
            tag_list=[]
        )
        return article

    async def test_create_comment(self, async_session: AsyncSession, sample_article: Article, sample_user: User):
        """Test creating a new comment."""
        service = CommentService(async_session)

        comment = await service.create_comment(
            slug=sample_article.slug,
            author=sample_user,
            body="This is a test comment"
        )

        assert comment.body == "This is a test comment"
        assert comment.article_id == sample_article.id
        assert comment.author_id == sample_user.id
        assert comment.id is not None

    async def test_get_comments_for_article(self, async_session: AsyncSession, sample_article: Article, sample_user: User):
        """Test getting comments for an article."""
        service = CommentService(async_session)

        # Create multiple comments
        await service.create_comment(sample_article.slug, sample_user, "First comment")
        await service.create_comment(sample_article.slug, sample_user, "Second comment")

        comments = await service.get_comments_for_article(sample_article.slug)

        assert len(comments) == 2
        # Comments should be ordered by creation date (newest first)
        assert comments[0].body == "Second comment"
        assert comments[1].body == "First comment"

    async def test_delete_comment(self, async_session: AsyncSession, sample_article: Article, sample_user: User):
        """Test deleting a comment."""
        service = CommentService(async_session)

        # Create comment
        comment = await service.create_comment(sample_article.slug, sample_user, "Test comment")

        # Delete comment
        result = await service.delete_comment(sample_article.slug, comment.id, sample_user)
        assert result is True

        # Verify comment is deleted
        comments = await service.get_comments_for_article(sample_article.slug)
        assert len(comments) == 0


@pytest.mark.asyncio
class TestArticleEndpoints:
    """Test article API endpoints."""

    def test_get_articles_endpoint(self, client: TestClient):
        """Test the GET /articles endpoint."""
        response = client.get("/articles")
        assert response.status_code == 200

        data = response.json()
        assert "articles" in data
        assert "articlesCount" in data
        assert isinstance(data["articles"], list)
        assert isinstance(data["articlesCount"], int)

    def test_get_articles_with_filters(self, client: TestClient):
        """Test GET /articles with query parameters."""
        response = client.get("/articles?limit=10&offset=0&tag=python")
        assert response.status_code == 200

        data = response.json()
        assert "articles" in data
        assert "articlesCount" in data

    def test_get_article_by_slug_not_found(self, client: TestClient):
        """Test GET /articles/{slug} with non-existent slug."""
        response = client.get("/articles/non-existent-slug")
        assert response.status_code == 404

    def test_get_feed_requires_auth(self, client: TestClient):
        """Test GET /articles/feed requires authentication."""
        response = client.get("/articles/feed")
        assert response.status_code == 401


class TestSlugGeneration:
    """Test slug generation functionality."""

    def test_slug_generation(self):
        """Test various slug generation scenarios."""
        from src.articles.service import slugify

        test_cases = [
            ("Simple Title", "simple-title"),
            ("Title with Numbers 123", "title-with-numbers-123"),
            ("Title!@#$%^&*()Special", "titlespecial"),
            ("Multiple    Spaces", "multiple-spaces"),
            ("Title-with-hyphens", "title-with-hyphens"),
            ("Title_with_underscores", "title_with_underscores"),
        ]

        for title, expected_slug in test_cases:
            assert slugify(title) == expected_slug
