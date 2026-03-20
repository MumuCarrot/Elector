"""HTTP API: /api/* (query votes in DB)."""

from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_get_votes_by_election_latest_per_voter(client, sqlite_engine_and_session_maker):
    from node.models.block import Block
    from node.models.transaction import Transaction
    from node.repositories.block_repository import BlockRepository

    async with sqlite_engine_and_session_maker() as session:
        repo = BlockRepository(session)
        last = await repo.get_last_block()
        assert last is not None

        t1 = Transaction(
            block_id=last.id,
            election_id="el-x",
            voter_id="same-voter",
            candidate_id="c-old",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        t2 = Transaction(
            block_id=last.id,
            election_id="el-x",
            voter_id="same-voter",
            candidate_id="c-new",
            created_at=datetime(2024, 6, 1, 12, 0, 0),
        )
        session.add_all([t1, t2])
        await session.commit()

    r = await client.get("/api/elid/el-x")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["votes"][0]["candidate_id"] == "c-new"


@pytest.mark.asyncio
async def test_get_votes_by_user(client, sqlite_engine_and_session_maker):
    from node.models.transaction import Transaction
    from node.repositories.block_repository import BlockRepository

    async with sqlite_engine_and_session_maker() as session:
        repo = BlockRepository(session)
        last = await repo.get_last_block()
        session.add(
            Transaction(
                block_id=last.id,
                election_id="el-y",
                voter_id="user-42",
                candidate_id="c1",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        await session.commit()

    r = await client.get("/api/uid/user-42")
    assert r.status_code == 200
    assert r.json()["count"] == 1


@pytest.mark.asyncio
async def test_get_user_vote_for_election_found_and_not_found(client, sqlite_engine_and_session_maker):
    from node.models.transaction import Transaction
    from node.repositories.block_repository import BlockRepository

    async with sqlite_engine_and_session_maker() as session:
        repo = BlockRepository(session)
        last = await repo.get_last_block()
        session.add(
            Transaction(
                block_id=last.id,
                election_id="el-z",
                voter_id="v-z",
                candidate_id="c-z",
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        await session.commit()

    r = await client.get("/api/elid/el-z/uid/v-z")
    assert r.status_code == 200
    assert r.json()["candidate_id"] == "c-z"

    missing = await client.get("/api/elid/el-z/uid/nobody")
    assert missing.status_code == 404
