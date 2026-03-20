"""HTTP API: /gossip/*"""

import pytest

from node.schemas.transaction import Transaction


@pytest.mark.asyncio
async def test_gossip_transactions_adds_to_mempool(client):
    txs = [
        Transaction(
            election_id="g-e1",
            voter_id="g-v1",
            candidate_id="g-c1",
        ).model_dump(mode="json")
    ]
    r = await client.post("/gossip/transactions", json=txs)
    assert r.status_code == 201
    assert r.json()["message"] == "Transactions received"


@pytest.mark.asyncio
async def test_gossip_chain_rejects_shorter_invalid(client):
    r = await client.post(
        "/gossip/chain",
        json={"chain": [], "tx_ids": []},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_gossip_neighbors(client):
    r = await client.post(
        "/gossip/neighbors",
        json=["10.0.0.5:5000"],
    )
    assert r.status_code == 201
    assert "10.0.0.5:5000" in r.json()["nodes"]
