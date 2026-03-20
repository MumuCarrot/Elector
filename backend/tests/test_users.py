import pytest


@pytest.mark.asyncio
async def test_create_user(client):
    r = await client.post(
        "/api/v1/users",
        json={
            "email": "apiuser@example.com",
            "password": "password12",
            "first_name": "Api",
            "last_name": "User",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "apiuser@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_users_paginated(client):
    await client.post(
        "/api/v1/users",
        json={
            "email": "u1@example.com",
            "password": "password12",
        },
    )
    r = await client.get("/api/v1/users?page=1&page_size=10")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_get_user_by_id(client):
    created = await client.post(
        "/api/v1/users",
        json={
            "email": "byid@example.com",
            "password": "password12",
        },
    )
    uid = created.json()["id"]
    r = await client.get(f"/api/v1/users/{uid}")
    assert r.status_code == 200
    assert r.json()["email"] == "byid@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(client):
    r = await client.get(
        "/api/v1/users/00000000-0000-0000-0000-000000000000"
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_user(client):
    created = await client.post(
        "/api/v1/users",
        json={
            "email": "upd@example.com",
            "password": "password12",
        },
    )
    uid = created.json()["id"]
    r = await client.put(
        f"/api/v1/users/{uid}",
        json={"first_name": "Updated"},
    )
    assert r.status_code == 200
    assert r.json()["first_name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_user(client):
    created = await client.post(
        "/api/v1/users",
        json={
            "email": "del@example.com",
            "password": "password12",
        },
    )
    uid = created.json()["id"]
    # Remove profile first (FK constraint; production DB may use ON DELETE CASCADE).
    await client.delete(f"/api/v1/user-profiles/user/{uid}")
    r = await client.delete(f"/api/v1/users/{uid}")
    assert r.status_code == 200
    g = await client.get(f"/api/v1/users/{uid}")
    assert g.status_code == 404
