"""Unit tests for Mempool (no database)."""

from node.schemas.transaction import Transaction
from node.services.mempool import Mempool


def test_mempool_add_and_contains():
    pool = Mempool()
    tx = Transaction(election_id="e1", voter_id="v1", candidate_id="c1")
    pool.new_transaction(tx)
    assert pool.contains(tx)
    assert len(pool.get_all()) == 1


def test_mempool_no_duplicate_same_id():
    pool = Mempool()
    tx = Transaction(
        id="fixed-id",
        election_id="e1",
        voter_id="v1",
        candidate_id="c1",
    )
    pool.new_transaction(tx)
    pool.new_transaction(tx)
    assert len(pool.get_all()) == 1


def test_mempool_remove_and_contains_all():
    pool = Mempool()
    a = Transaction(election_id="e1", voter_id="v1", candidate_id="c1")
    b = Transaction(election_id="e1", voter_id="v2", candidate_id="c2")
    pool.new_transactions([a, b])
    assert pool.contains_all([a, b])
    pool.remove([a])
    assert not pool.contains(a)
    assert pool.contains(b)


def test_get_block_transaction_respects_limit():
    pool = Mempool()
    for i in range(5):
        pool.new_transaction(
            Transaction(election_id="e1", voter_id=f"v{i}", candidate_id="c1")
        )
    batch = pool.get_block_transaction(limit=3)
    assert len(batch) == 3
