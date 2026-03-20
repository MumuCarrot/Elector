import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app


@pytest.mark.asyncio
async def test_health_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("detail") == "ok"
    assert data.get("result") == "working"


@pytest.mark.asyncio
async def test_health_postgresql_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/postgresql")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


@pytest.mark.asyncio
async def test_health_redis_ok(monkeypatch):
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.close = AsyncMock()
    monkeypatch.setattr("app.routers.healthcheck.redis_client", mock_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/health/redis")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"


@pytest.mark.asyncio
async def test_health_protected_requires_auth(client):
    r = await client.get("/api/v1/health/protected")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_health_protected_with_auth(auth_client):
    r = await auth_client.get("/api/v1/health/protected")
    assert r.status_code == 200
    data = r.json()
    assert data.get("authenticated") is True
    assert "user_id" in data
