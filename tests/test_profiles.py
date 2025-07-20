import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
import uuid

from src.users.models import User, user_follows
from src.profiles.service import ProfileService


class TestProfiles:
    """Test suite for the profiles module."""

    def test_get_profile_endpoint(self, client: TestClient, test_user: User):
        """Test the GET /profiles/{username} endpoint."""
        response = client.get(f"/profiles/{test_user.username}")
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == test_user.username
        assert data["bio"] == test_user.bio
        assert data["image"] == test_user.image
        assert data["following"] is False  # Not authenticated

    def test_get_nonexistent_profile(self, client: TestClient):
        """Test getting a non-existent profile returns 404."""
        response = client.get("/profiles/nonexistent")
        assert response.status_code == 404
        assert "Profile not found" in response.json()["detail"]

    import pytest


class TestProfiles:
    """Test suite for the profiles module."""

    def test_get_profile_endpoint(self, client: TestClient, test_user: User):
        """Test the GET /profiles/{username} endpoint."""
        response = client.get(f"/profiles/{test_user.username}")
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == test_user.username
        assert data["bio"] == test_user.bio
        assert data["image"] == test_user.image
        assert data["following"] is False  # Not authenticated

    def test_get_nonexistent_profile(self, client: TestClient):
        """Test getting a non-existent profile returns 404."""
        response = client.get("/profiles/nonexistent")
        assert response.status_code == 404
        assert "Profile not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestProfileService:
    """Test ProfileService methods."""

    async def test_get_profile_by_username(self, async_session: AsyncSession, test_user: User):
        """Test getting profile by username."""
        service = ProfileService(async_session)

        # Test existing user
        profile = await service.get_profile_by_username(test_user.username)
        assert profile is not None
        assert profile.username == test_user.username
        assert profile.bio == test_user.bio
        assert profile.image == test_user.image

        # Test non-existing user
        profile = await service.get_profile_by_username("nonexistent")
        assert profile is None

    async def test_get_profile_with_following_status(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test getting profile with following status."""
        service = ProfileService(async_session)

        # Initially not following
        profile = await service.get_profile_by_username(other_user.username, test_user)
        assert profile.is_following is False

        # Create follow relationship
        await async_session.execute(
            user_follows.insert().values(
                follower_id=test_user.id,
                followed_id=other_user.id
            )
        )
        await async_session.commit()

        # Now should be following
        profile = await service.get_profile_by_username(other_user.username, test_user)
        assert profile.is_following is True

    async def test_update_profile(self, async_session: AsyncSession, test_user: User):
        """Test updating user profile."""
        service = ProfileService(async_session)

        # Update all fields
        updated_user = await service.update_profile(
            test_user,
            username="newusername",
            bio="New bio",
            image="https://example.com/new.jpg"
        )

        assert updated_user.username == "newusername"
        assert updated_user.bio == "New bio"
        assert updated_user.image == "https://example.com/new.jpg"

        # Update partial fields
        updated_user = await service.update_profile(
            updated_user,
            bio="Updated bio only"
        )

        assert updated_user.username == "newusername"  # unchanged
        assert updated_user.bio == "Updated bio only"
        assert updated_user.image == "https://example.com/new.jpg"  # unchanged

    async def test_follow_user(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test following a user."""
        service = ProfileService(async_session)

        # Follow user
        followed_user = await service.follow_user(test_user, other_user.username)

        assert followed_user.id == other_user.id
        assert followed_user.is_following is True

        # Verify follow relationship exists in database
        is_following = await service._is_following(test_user.id, other_user.id)
        assert is_following is True

    async def test_unfollow_user(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test unfollowing a user."""
        service = ProfileService(async_session)

        # First follow the user
        await service.follow_user(test_user, other_user.username)

        # Then unfollow
        unfollowed_user = await service.unfollow_user(test_user, other_user.username)

        assert unfollowed_user.id == other_user.id
        assert unfollowed_user.is_following is False

        # Verify follow relationship no longer exists in database
        is_following = await service._is_following(test_user.id, other_user.id)
        assert is_following is False


class TestProfileSchemas:
    """Test profile schema validation."""

    def test_profile_response_schema(self):
        """Test ProfileResponse schema."""
        from src.profiles.schemas import ProfileResponse

        profile_data = {
            "username": "testuser",
            "bio": "Test bio",
            "image": "https://example.com/image.jpg",
            "following": True
        }

        profile = ProfileResponse(**profile_data)
        assert profile.username == "testuser"
        assert profile.bio == "Test bio"
        assert profile.image == "https://example.com/image.jpg"
        assert profile.following is True

    def test_profile_update_schema_validation(self):
        """Test ProfileUpdate schema validation."""
        from src.profiles.schemas import ProfileUpdate

        # Valid username
        update = ProfileUpdate(username="validuser123")
        assert update.username == "validuser123"

        # Username with underscores and hyphens
        update = ProfileUpdate(username="user_name-123")
        assert update.username == "user_name-123"

        # Username should be lowercase
        update = ProfileUpdate(username="UserName")
        assert update.username == "username"  # Converted to lowercase

    def test_profile_update_invalid_username(self):
        """Test ProfileUpdate schema with invalid usernames."""
        from src.profiles.schemas import ProfileUpdate
        from pydantic import ValidationError

        # Username with invalid characters
        with pytest.raises(ValidationError):
            ProfileUpdate(username="user@name")

        # Username starting with underscore
        with pytest.raises(ValidationError):
            ProfileUpdate(username="_username")

        # Username ending with hyphen
        with pytest.raises(ValidationError):
            ProfileUpdate(username="username-")

        # Username too short
        with pytest.raises(ValidationError):
            ProfileUpdate(username="ab")


class TestUserModelValidation:
    """Test User model validation with username."""

    def test_username_validation_in_auth_schemas(self):
        """Test username validation in auth schemas."""
        from src.auth.schemas import UserCreate, UserUpdate
        from pydantic import ValidationError

        # Valid user creation
        user_create = UserCreate(
            email="test@example.com",
            password="password123",
            username="testuser"
        )
        assert user_create.username == "testuser"

        # Username validation in update
        user_update = UserUpdate(username="newusername")
        assert user_update.username == "newusername"

        # Invalid username should raise error
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="password123",
                username="user@name"  # Invalid character
            )

    async def test_get_profile_with_following_status(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test getting profile with following status."""
        service = ProfileService(async_session)

        # Initially not following
        profile = await service.get_profile_by_username(other_user.username, test_user)
        assert profile.is_following is False

        # Create follow relationship
        await async_session.execute(
            user_follows.insert().values(
                follower_id=test_user.id,
                followed_id=other_user.id
            )
        )
        await async_session.commit()

        # Now should be following
        profile = await service.get_profile_by_username(other_user.username, test_user)
        assert profile.is_following is True

    async def test_update_profile(self, async_session: AsyncSession, test_user: User):
        """Test updating user profile."""
        service = ProfileService(async_session)

        # Update all fields
        updated_user = await service.update_profile(
            test_user,
            username="newusername",
            bio="New bio",
            image="https://example.com/new.jpg"
        )

        assert updated_user.username == "newusername"
        assert updated_user.bio == "New bio"
        assert updated_user.image == "https://example.com/new.jpg"

        # Update partial fields
        updated_user = await service.update_profile(
            updated_user,
            bio="Updated bio only"
        )

        assert updated_user.username == "newusername"  # unchanged
        assert updated_user.bio == "Updated bio only"
        assert updated_user.image == "https://example.com/new.jpg"  # unchanged

    async def test_update_profile_duplicate_username(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test updating profile with duplicate username raises error."""
        service = ProfileService(async_session)

        with pytest.raises(Exception):  # Should raise HTTPException with 422 status
            await service.update_profile(
                test_user,
                username=other_user.username  # Try to use existing username
            )

    async def test_follow_user(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test following a user."""
        service = ProfileService(async_session)

        # Follow user
        followed_user = await service.follow_user(test_user, other_user.username)

        assert followed_user.id == other_user.id
        assert followed_user.is_following is True

        # Verify follow relationship exists in database
        is_following = await service._is_following(test_user.id, other_user.id)
        assert is_following is True

    async def test_follow_nonexistent_user(self, async_session: AsyncSession, test_user: User):
        """Test following a non-existent user raises error."""
        service = ProfileService(async_session)

        with pytest.raises(Exception):  # Should raise HTTPException with 404 status
            await service.follow_user(test_user, "nonexistentuser")

    async def test_follow_self(self, async_session: AsyncSession, test_user: User):
        """Test following self raises error."""
        service = ProfileService(async_session)

        with pytest.raises(Exception):  # Should raise HTTPException with 422 status
            await service.follow_user(test_user, test_user.username)

    async def test_follow_already_following(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test following user already being followed raises error."""
        service = ProfileService(async_session)

        # First follow
        await service.follow_user(test_user, other_user.username)

        # Try to follow again
        with pytest.raises(Exception):  # Should raise HTTPException with 422 status
            await service.follow_user(test_user, other_user.username)

    async def test_unfollow_user(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test unfollowing a user."""
        service = ProfileService(async_session)

        # First follow the user
        await service.follow_user(test_user, other_user.username)

        # Then unfollow
        unfollowed_user = await service.unfollow_user(test_user, other_user.username)

        assert unfollowed_user.id == other_user.id
        assert unfollowed_user.is_following is False

        # Verify follow relationship no longer exists in database
        is_following = await service._is_following(test_user.id, other_user.id)
        assert is_following is False

    async def test_unfollow_not_following(
        self,
        async_session: AsyncSession,
        test_user: User,
        other_user: User
    ):
        """Test unfollowing user not being followed raises error."""
        service = ProfileService(async_session)

        with pytest.raises(Exception):  # Should raise HTTPException with 422 status
            await service.unfollow_user(test_user, other_user.username)


class TestProfileSchemas:
    """Test profile schema validation."""

    def test_profile_response_schema(self):
        """Test ProfileResponse schema."""
        from src.profiles.schemas import ProfileResponse

        profile_data = {
            "username": "testuser",
            "bio": "Test bio",
            "image": "https://example.com/image.jpg",
            "following": True
        }

        profile = ProfileResponse(**profile_data)
        assert profile.username == "testuser"
        assert profile.bio == "Test bio"
        assert profile.image == "https://example.com/image.jpg"
        assert profile.following is True

    def test_profile_update_schema_validation(self):
        """Test ProfileUpdate schema validation."""
        from src.profiles.schemas import ProfileUpdate

        # Valid username
        update = ProfileUpdate(username="validuser123")
        assert update.username == "validuser123"

        # Username with underscores and hyphens
        update = ProfileUpdate(username="user_name-123")
        assert update.username == "user_name-123"

        # Username should be lowercase
        update = ProfileUpdate(username="UserName")
        assert update.username == "username"  # Converted to lowercase

    def test_profile_update_invalid_username(self):
        """Test ProfileUpdate schema with invalid usernames."""
        from src.profiles.schemas import ProfileUpdate
        from pydantic import ValidationError

        # Username with invalid characters
        with pytest.raises(ValidationError):
            ProfileUpdate(username="user@name")

        # Username starting with underscore
        with pytest.raises(ValidationError):
            ProfileUpdate(username="_username")

        # Username ending with hyphen
        with pytest.raises(ValidationError):
            ProfileUpdate(username="username-")

        # Username too short
        with pytest.raises(ValidationError):
            ProfileUpdate(username="ab")


class TestUserModelValidation:
    """Test User model validation with username."""

    def test_username_validation_in_auth_schemas(self):
        """Test username validation in auth schemas."""
        from src.auth.schemas import UserCreate, UserUpdate
        from pydantic import ValidationError

        # Valid user creation
        user_create = UserCreate(
            email="test@example.com",
            password="password123",
            username="testuser"
        )
        assert user_create.username == "testuser"

        # Username validation in update
        user_update = UserUpdate(username="newusername")
        assert user_update.username == "newusername"

        # Invalid username should raise error
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="password123",
                username="user@name"  # Invalid character
            )


@pytest.fixture
async def async_session():
    """Async session fixture for testing."""
    # This would typically be set up with a test database
    # For now, we'll use a mock or skip database-dependent tests
    pass
