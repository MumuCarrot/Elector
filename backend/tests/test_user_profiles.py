import pytest


@pytest.mark.asyncio
async def test_get_my_profile(auth_client):
    r = await auth_client.get("/api/v1/user-profiles/me/profile")
    assert r.status_code == 200
    body = r.json()
    assert "user_id" in body
    assert "id" in body


@pytest.mark.asyncio
async def test_update_my_profile(auth_client):
    r = await auth_client.put(
        "/api/v1/user-profiles/me/profile",
        json={"address": "Kyiv, UA"},
    )
    assert r.status_code == 200
    assert r.json().get("address") == "Kyiv, UA"


@pytest.mark.asyncio
async def test_get_profile_by_user_id(auth_client):
    me = await auth_client.get("/api/v1/auth/me")
    uid = me.json()["id"]
    r = await auth_client.get(f"/api/v1/user-profiles/user/{uid}")
    assert r.status_code == 200
    assert r.json()["user_id"] == uid


@pytest.mark.asyncio
async def test_list_profiles_paginated(client):
    await client.post(
        "/api/v1/users",
        json={"email": "prof@example.com", "password": "password12"},
    )
    r = await client.get("/api/v1/user-profiles?page=1&page_size=10")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_get_profile_by_profile_id(auth_client):
    me_prof = await auth_client.get("/api/v1/user-profiles/me/profile")
    pid = me_prof.json()["id"]
    r = await auth_client.get(f"/api/v1/user-profiles/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid


@pytest.mark.asyncio
async def test_delete_my_profile(auth_client):
    r = await auth_client.delete("/api/v1/user-profiles/me/profile")
    assert r.status_code == 200
    g = await auth_client.get("/api/v1/user-profiles/me/profile")
    assert g.status_code == 404
