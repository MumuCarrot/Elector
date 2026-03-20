import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "password12",
                "first_name": "N",
                "last_name": "W",
            },
        )
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "new@example.com"
    assert r.cookies.get("access_token")


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict():
    transport = ASGITransport(app=app)
    payload = {
        "email": "dup@example.com",
        "password": "password12",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "password12",
            },
        )
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "password12"},
        )
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "login@example.com"
    assert r.cookies.get("access_token")


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password12"},
        )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_authentication(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user(auth_client):
    r = await auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_refresh_tokens():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "password12",
            },
        )
        assert reg.status_code == 201
        r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    assert "detail" in r.json()


@pytest.mark.asyncio
async def test_logout():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "password12",
            },
        )
        r = await client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    assert r.json().get("detail") == "Logged out successfully"
