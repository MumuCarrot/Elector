from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from node.dependencies import get_session
from node.models.transaction import Transaction
from node.repositories.transaction_repository import TransactionRepository

router = APIRouter(tags=["api_addons"])


def _tx_to_dict(tx) -> dict:
    """Serializes a SQLAlchemy ``Transaction`` row for JSON.

    Args:
        tx: ORM transaction instance.

    Returns:
        dict: Id, election, voter, candidate, and ISO ``created_at``.

    """
    return {
        "id": tx.id,
        "election_id": tx.election_id,
        "voter_id": tx.voter_id,
        "candidate_id": tx.candidate_id,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }


@router.get("/elid/{election_id}")
async def get_votes_by_election(
    election_id: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Returns latest vote per voter for an election (by ``created_at``).

    Args:
        election_id: Election identifier.
        session: DB session.

    Returns:
        JSONResponse: ``votes`` and ``count``.

    """
    repo = TransactionRepository(session)
    transactions = await repo.get_by_election_id(election_id)

    voter_to_latest: dict[str, Transaction] = {}
    for tx in transactions:
        prev = voter_to_latest.get(tx.voter_id)
        if prev is None or (
            tx.created_at
            and (prev.created_at is None or tx.created_at > prev.created_at)
        ):
            voter_to_latest[tx.voter_id] = tx

    votes = [_tx_to_dict(tx) for tx in voter_to_latest.values()]
    return JSONResponse(content={"votes": votes, "count": len(votes)})


@router.get("/uid/{user_id}")
async def get_votes_by_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Returns all on-chain votes for a voter id.

    Args:
        user_id: Voter (user) identifier.
        session: DB session.

    Returns:
        JSONResponse: ``votes`` and ``count``.

    """
    repo = TransactionRepository(session)
    transactions = await repo.get_by_voter_id(user_id)
    votes = [_tx_to_dict(tx) for tx in transactions]
    return JSONResponse(content={"votes": votes, "count": len(votes)})


@router.get("/elid/{election_id}/uid/{user_id}")
async def get_user_vote_for_election(
    election_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Returns one vote for a user in an election, or 404.

    Args:
        election_id: Election identifier.
        user_id: Voter identifier.
        session: DB session.

    Returns:
        JSONResponse: Vote dict or 404 JSON error.

    """
    repo = TransactionRepository(session)
    tx = await repo.get_by_election_and_voter(election_id, user_id)
    if not tx:
        return JSONResponse(
            content={"detail": "Vote not found"},
            status_code=404,
        )
    return JSONResponse(content=_tx_to_dict(tx))
