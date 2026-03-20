from __future__ import annotations

import os

# Generate RSA keys before any app import (JWT settings load at import time).
if not os.environ.get("AUTH_PRIVATE_KEY"):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    _key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _priv = _key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    _pub = _key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    os.environ["AUTH_PRIVATE_KEY"] = _priv.decode()
    os.environ["AUTH_PUBLIC_KEY"] = _pub.decode()

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.main import app


@pytest.fixture(autouse=True)
def mock_jwt_redis_cache(monkeypatch):
    """In-memory stand-in for Redis blacklist used by JWT utils."""
    store: dict[str, str] = {}

    async def set_cache(key: str, value: str, expire: int = 60) -> None:
        store[key] = value

    async def get_cache(key: str):
        return store.get(key)

    monkeypatch.setattr("app.utils.jwt.set_cache", set_cache)
    monkeypatch.setattr("app.utils.jwt.get_cache", get_cache)
    yield
    store.clear()


@pytest_asyncio.fixture(autouse=True)
async def test_engine_and_session(monkeypatch):
    """SQLite in-memory DB, shared connection; patch all async_session_maker imports."""
    import app.db.database as db_mod
    import app.dependencies.database as db_dep
    import app.routers.healthcheck as hc_mod

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    monkeypatch.setattr(db_mod, "engine", engine)
    monkeypatch.setattr(db_mod, "async_session_maker", TestingSessionLocal)
    monkeypatch.setattr(db_dep, "async_session_maker", TestingSessionLocal)
    monkeypatch.setattr(hc_mod, "async_session_maker", TestingSessionLocal)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=True
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """Registered user with cookies set."""
    payload = {
        "email": "testuser@example.com",
        "password": "password12",
        "first_name": "Test",
        "last_name": "User",
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return client


@pytest.fixture
def election_payload():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return {
        "title": "Test election",
        "description": "Desc",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=7)).isoformat(),
        "is_public": True,
        "candidates": [
            {"name": "Candidate A", "description": "A"},
            {"name": "Candidate B", "description": "B"},
        ],
        "settings": {
            "allow_revoting": False,
            "max_votes": 1,
            "require_auth": True,
            "anonymous": False,
        },
    }
