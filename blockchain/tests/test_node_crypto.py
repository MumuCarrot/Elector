"""Proof-of-work and hashing helpers on Node."""

from datetime import datetime

import pytest

from node.schemas.transaction import Transaction
from node.services.node import Node


def test_valid_nonce_fails_when_difficulty_impossible(monkeypatch):
    monkeypatch.setattr(
        "node.services.node.settings.app.PROOF_OF_WORK_DIFFICULTY", "zzzz"
    )
    txs = [Transaction(election_id="e1", voter_id="v1", candidate_id="c1")]
    assert not Node.valid_nonce(
        index=2,
        transactions=txs,
        last_nonce=100,
        previous_hash="ab" * 16,
        timestamp=1.0,
        nonce=12345,
    )


def test_hash_is_deterministic():
    txs = [Transaction(election_id="e1", voter_id="v1", candidate_id="c1")]
    ts = datetime(2020, 1, 1, 0, 0, 0)
    h1 = Node._block_hash(1, ts, txs, 100, "0" * 32)
    h2 = Node._block_hash(1, ts, txs, 100, "0" * 32)
    assert h1 == h2
    assert len(h1) == 64


@pytest.mark.asyncio
async def test_valid_chain_genesis_only(client, blockchain_node, sqlite_engine_and_session_maker):
    async with sqlite_engine_and_session_maker() as session:
        chain = await blockchain_node.get_chain(session)
        assert len(chain) >= 1
        assert await blockchain_node.valid_chain(session=session)
