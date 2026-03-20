import pytest


@pytest.fixture
def mock_blockchain_create_tx(monkeypatch):
    async def create_transaction(
        election_id: str,
        voter_id: str,
        candidate_id: str | None = None,
        created_at=None,
    ):
        return {
            "transaction_id": "11111111-1111-1111-1111-111111111111",
            "election_id": election_id,
            "voter_id": voter_id,
            "candidate_id": candidate_id,
            "created_at": "2025-06-01T10:00:00+00:00",
        }

    monkeypatch.setattr("app.services.vote.create_transaction", create_transaction)


@pytest.mark.asyncio
async def test_create_vote_success(
    auth_client, election_payload, mock_blockchain_create_tx
):
    el = await auth_client.post("/api/v1/elections", json=election_payload)
    assert el.status_code == 201
    election_id = el.json()["id"]
    candidate_id = el.json()["candidates"][0]["id"]

    r = await auth_client.post(
        "/api/v1/votes",
        json={
            "election_id": election_id,
            "candidate_id": candidate_id,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["election_id"] == election_id
    assert body["candidate_id"] == candidate_id


@pytest.mark.asyncio
async def test_create_votes_batch(
    auth_client, election_payload, mock_blockchain_create_tx, monkeypatch
):
    payload = {
        **election_payload,
        "settings": {
            **election_payload["settings"],
            "max_votes": 2,
        },
    }
    el = await auth_client.post("/api/v1/elections", json=payload)
    assert el.status_code == 201
    election_id = el.json()["id"]
    c_ids = [c["id"] for c in el.json()["candidates"]]

    r = await auth_client.post(
        "/api/v1/votes/batch",
        json={
            "election_id": election_id,
            "candidate_ids": c_ids,
        },
    )
    assert r.status_code == 201, r.text
    assert len(r.json()["votes"]) == 2


@pytest.mark.asyncio
async def test_request_token_rejected_for_non_anonymous_election(
    auth_client, election_payload
):
    el = await auth_client.post("/api/v1/elections", json=election_payload)
    election_id = el.json()["id"]
    r = await auth_client.post(
        f"/api/v1/votes/election/{election_id}/request-token"
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_anonymous_vote_flow(
    auth_client, election_payload, mock_blockchain_create_tx
):
    payload = {
        **election_payload,
        "settings": {
            **election_payload["settings"],
            "anonymous": True,
        },
    }
    el = await auth_client.post("/api/v1/elections", json=payload)
    assert el.status_code == 201
    election_id = el.json()["id"]
    candidate_id = el.json()["candidates"][0]["id"]

    tok = await auth_client.post(
        f"/api/v1/votes/election/{election_id}/request-token"
    )
    assert tok.status_code == 200
    token = tok.json()["token"]

    r = await auth_client.post(
        "/api/v1/votes",
        json={
            "election_id": election_id,
            "candidate_id": candidate_id,
            "anonymous_token": token,
        },
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_election_results_aggregated(
    auth_client, election_payload, monkeypatch
):
    el = await auth_client.post("/api/v1/elections", json=election_payload)
    election_id = el.json()["id"]
    cid = el.json()["candidates"][0]["id"]

    async def get_votes_by_election(eid: str):
        assert eid == election_id
        return {
            "votes": [
                {"candidate_id": cid},
                {"candidate_id": cid},
            ]
        }

    monkeypatch.setattr(
        "app.services.vote.get_votes_by_election",
        get_votes_by_election,
    )

    r = await auth_client.get(
        f"/api/v1/votes/election/{election_id}/results"
    )
    assert r.status_code == 200
    assert r.json()[cid] == 2


@pytest.mark.asyncio
async def test_get_my_vote(
    auth_client, election_payload, monkeypatch
):
    el = await auth_client.post("/api/v1/elections", json=election_payload)
    election_id = el.json()["id"]
    me = await auth_client.get("/api/v1/auth/me")
    uid = me.json()["id"]
    cid = el.json()["candidates"][0]["id"]

    async def get_user_vote_for_election(eid: str, user_id: str):
        return {
            "id": "tx-1",
            "election_id": eid,
            "voter_id": user_id,
            "candidate_id": cid,
            "created_at": None,
        }

    monkeypatch.setattr(
        "app.services.vote.get_user_vote_for_election",
        get_user_vote_for_election,
    )

    r = await auth_client.get(
        f"/api/v1/votes/election/{election_id}/my-vote"
    )
    assert r.status_code == 200
    assert r.json()["candidate_id"] == cid


@pytest.mark.asyncio
async def test_get_votes_by_user_same_user_only(
    auth_client, monkeypatch
):
    me = await auth_client.get("/api/v1/auth/me")
    uid = me.json()["id"]

    async def get_votes_by_user(user_id: str):
        return [
            {
                "id": "1",
                "election_id": "e1",
                "voter_id": user_id,
                "candidate_id": "c1",
                "created_at": None,
            }
        ]

    monkeypatch.setattr(
        "app.services.vote.get_votes_by_user",
        get_votes_by_user,
    )

    r = await auth_client.get(f"/api/v1/votes/user/{uid}")
    assert r.status_code == 200
    assert len(r.json()["votes"]) == 1


@pytest.mark.asyncio
async def test_get_votes_by_user_forbidden_for_other_user(auth_client):
    me = await auth_client.get("/api/v1/auth/me")
    uid = me.json()["id"]
    other = "99999999-9999-9999-9999-999999999999"
    assert uid != other
    r = await auth_client.get(f"/api/v1/votes/user/{other}")
    assert r.status_code == 403
