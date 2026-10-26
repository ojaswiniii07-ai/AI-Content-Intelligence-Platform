import sys
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Add Backend to python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.security import create_access_token
from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an asynchronous HTTP test client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict:
    """Provides valid JWT Bearer authentication headers for test queries."""
    token = create_access_token(
        subject="usr_test_admin",
        extra_claims={
            "email": "ojaswini@org.com",
            "name": "Ojaswini",
            "role": "admin",
        },
    )
    return {"Authorization": f"Bearer {token}"}
