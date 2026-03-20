"""HTTP API: /blockchain/*"""

import pytest


@pytest.mark.asyncio
async def test_chain_returns_genesis(client):
    r = await client.get("/blockchain/chain")
    assert r.status_code == 200
    data = r.json()
    assert data["length"] == 1
    assert len(data["chain"]) == 1
    assert data["chain"][0]["index"] == 1


@pytest.mark.asyncio
async def test_chain_registers_peer_query_param(client):
    r = await client.get(
        "/blockchain/chain",
        params={"node_address": "192.168.1.10:5001"},
    )
    assert r.status_code == 200
    nodes = await client.get("/blockchain/nodes")
    assert "192.168.1.10:5001" in nodes.json()["nodes"]


@pytest.mark.asyncio
async def test_new_transaction_and_mempool_list(client):
    body = {
        "election_id": "election-1",
        "voter_id": "voter-1",
        "candidate_id": "candidate-1",
    }
    r = await client.post("/blockchain/transactions/new", json=body)
    assert r.status_code == 201
    out = r.json()
    assert out["election_id"] == "election-1"
    assert "transaction_id" in out

    lst = await client.get("/blockchain/transactions")
    assert lst.status_code == 200
    assert lst.json()["count"] == 1


@pytest.mark.asyncio
async def test_mining_cycle_adds_block(client, blockchain_node, sqlite_engine_and_session_maker):
    await client.post(
        "/blockchain/transactions/new",
        json={
            "election_id": "e-mine",
            "voter_id": "v-mine",
            "candidate_id": "c-mine",
        },
    )
    async with sqlite_engine_and_session_maker() as session:
        blockchain_node.session = session
        await blockchain_node._mining_cycle(session)

    ch = await client.get("/blockchain/chain")
    assert ch.status_code == 200
    assert ch.json()["length"] == 2


@pytest.mark.asyncio
async def test_nodes_list_initially_empty_or_main_only(client):
    r = await client.get("/blockchain/nodes")
    assert r.status_code == 200
    assert "nodes" in r.json()
    assert "count" in r.json()
