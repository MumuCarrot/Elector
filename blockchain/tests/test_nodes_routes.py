"""HTTP API: /nodes/*"""

import pytest


@pytest.mark.asyncio
async def test_register_nodes(client):
    r = await client.post(
        "/nodes/register",
        json={"nodes": ["10.0.0.1:5000", "10.0.0.2:5000"]},
    )
    assert r.status_code == 201
    data = r.json()
    assert "10.0.0.1:5000" in data["total_nodes"]


@pytest.mark.asyncio
async def test_resolve_conflicts_returns_authoritative(client):
    r = await client.post("/nodes/resolve")
    assert r.status_code == 200
    body = r.json()
    assert "message" in body
    assert "chain" in body or "new_chain" in body
