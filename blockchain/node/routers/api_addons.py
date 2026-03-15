from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from node.dependencies import get_session
from node.models.transaction import Transaction
from node.repositories.transaction_repository import TransactionRepository

router = APIRouter(tags=["api_addons"])


def _tx_to_dict(tx) -> dict:
    """Convert Transaction model to JSON-serializable dict."""
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
    """Get all votes for an election. Only the latest vote per voter is returned (repeated votes overwrite previous)."""

    repo = TransactionRepository(session)
    transactions = await repo.get_by_election_id(election_id)

    # Keep only the latest vote per voter_id (by created_at)
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
    """Get all votes by a user (DB query by voter_id)."""

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
    """Get user's vote for a specific election (DB query by election_id + voter_id)."""
    
    repo = TransactionRepository(session)
    tx = await repo.get_by_election_and_voter(election_id, user_id)
    if not tx:
        return JSONResponse(
            content={"detail": "Vote not found"},
            status_code=404,
        )
    return JSONResponse(content=_tx_to_dict(tx))