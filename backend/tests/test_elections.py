import pytest


@pytest.mark.asyncio
async def test_create_election_requires_auth(client, election_payload):
    r = await client.post("/api/v1/elections", json=election_payload)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_election_success(auth_client, election_payload):
    r = await auth_client.post("/api/v1/elections", json=election_payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == election_payload["title"]
    assert len(data["candidates"]) == 2
    assert data["settings"] is not None


@pytest.mark.asyncio
async def test_list_elections_empty(client):
    r = await client.get("/api/v1/elections")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_elections_after_create(auth_client, election_payload):
    await auth_client.post("/api/v1/elections", json=election_payload)
    r = await auth_client.get("/api/v1/elections?page=1&page_size=10")
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_get_election_by_id(auth_client, election_payload):
    created = await auth_client.post("/api/v1/elections", json=election_payload)
    eid = created.json()["id"]
    r = await auth_client.get(f"/api/v1/elections/{eid}")
    assert r.status_code == 200
    assert r.json()["id"] == eid


@pytest.mark.asyncio
async def test_get_election_not_found(client):
    r = await client.get(
        "/api/v1/elections/00000000-0000-0000-0000-000000000000"
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_election(auth_client, election_payload):
    created = await auth_client.post("/api/v1/elections", json=election_payload)
    eid = created.json()["id"]
    r = await auth_client.put(
        f"/api/v1/elections/{eid}",
        json={"title": "Updated title"},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Updated title"


@pytest.mark.asyncio
async def test_delete_election(auth_client, election_payload):
    created = await auth_client.post("/api/v1/elections", json=election_payload)
    eid = created.json()["id"]
    r = await auth_client.delete(f"/api/v1/elections/{eid}")
    assert r.status_code == 200
    g = await auth_client.get(f"/api/v1/elections/{eid}")
    assert g.status_code == 404
