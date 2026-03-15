from typing import Optional

from app.core.logging_config import get_logger
from app.schemas.vote import VoteCreate, VoteUpdate, VoteResponse
from app.services.blockchain_client import (
    create_transaction,
    get_votes_by_election,
    get_votes_by_user,
    get_user_vote_for_election,
)

logger = get_logger("vote_service")


class VoteService:
    """Service for vote CRUD operations."""

    @staticmethod
    async def create_vote(
        vote_data: VoteCreate, user_id: str
    ) -> VoteResponse:
        """Create a new vote by sending a transaction to the blockchain."""
        
        result = await create_transaction(
            election_id=vote_data.election_id,
            voter_id=user_id,
            candidate_id=vote_data.candidate_id,
        )
        return VoteResponse(
            id=result.get("transaction_id"),
            election_id=vote_data.election_id,
            voter_id=user_id,
            candidate_id=vote_data.candidate_id,
            created_at=result.get("created_at"),
        )


    @staticmethod
    async def get_results_by_election(
        election_id: str
    ) -> dict:
        """Get all votes for a specific election."""

        votes = await get_votes_by_election(election_id)
        results = {}
        for vote in votes.get("votes", []):
            candidate_id = vote.get("candidate_id")
            results[candidate_id] = results.get(candidate_id, 0) + 1
        return results

    @staticmethod
    async def get_votes_by_user(
        user_id: str
        ) -> list[VoteResponse]:
        """Get all votes by a specific user from blockchain."""
        
        transactions = await get_votes_by_user(user_id)
        return [
            VoteResponse(
                id=tx.get("id", ""),
                election_id=tx.get("election_id", ""),
                voter_id=tx.get("voter_id", ""),
                candidate_id=tx.get("candidate_id"),
                created_at=tx.get("created_at"),
            )
            for tx in transactions
        ]

    @staticmethod
    async def get_user_vote_for_election(
        election_id: str, user_id: str
    ) -> Optional[VoteResponse]:
        """Get user's vote for a specific election from blockchain."""

        tx = await get_user_vote_for_election(election_id, user_id)
        if not tx:
            return None
        return VoteResponse(
            id=tx.get("id", ""),
            election_id=tx.get("election_id", ""),
            voter_id=tx.get("voter_id", ""),
            candidate_id=tx.get("candidate_id"),
            created_at=tx.get("created_at"),
        )

vote_service = VoteService()
