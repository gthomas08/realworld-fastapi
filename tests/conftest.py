from src.database import Base
from src.main import app
from unittest.mock import AsyncMock
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from fastapi.testclient import TestClient
import pytest_asyncio
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest_asyncio.fixture
async def mock_async_session():
    """Create a mock async session for testing."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session
