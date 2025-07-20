import pytest
from fastapi.testclient import TestClient

from src.tags.schemas import TagsResponse


class TestTagSchemas:
    """Test tag schema validation."""
    
    def test_tags_response_schema(self):
        """Test TagsResponse schema."""
        response = TagsResponse(tags=["python", "javascript", "react"])
        assert len(response.tags) == 3
        assert "python" in response.tags
