from src.main import app
from src.tags.schemas import TagsResponse
from src.tags.service import TagService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTagService:
    """Unit tests for TagService."""

    @pytest.mark.asyncio
    async def test_get_all_tags(self, mock_async_session):
        """Test getting all tags from service."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            "python", "javascript", "react"]
        mock_async_session.execute.return_value = mock_result

        service = TagService(mock_async_session)

        # Act
        tags = await service.get_all_tags()

        # Assert
        assert tags == ["python", "javascript", "react"]
        mock_async_session.execute.assert_called_once()


class TestTagsEndpoint:
    """Integration tests for tags API endpoint."""

    def test_get_tags_endpoint(self, client: TestClient):
        """Test GET /tags endpoint returns correct response structure."""
        # Act
        response = client.get("/tags")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert isinstance(data["tags"], list)


class TestTagSchemas:
    """Test tag schema validation."""

    def test_tags_response_schema(self):
        """Test TagsResponse schema."""
        response = TagsResponse(tags=["python", "javascript", "react"])
        assert len(response.tags) == 3
        assert "python" in response.tags
