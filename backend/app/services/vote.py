from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.exceptions.user import ValidationError
from app.models.election_setting import ElectionSetting
from app.repository.anonymous_vote_token_repository import AnonymousVoteTokenRepository
from app.repository.election_setting_repository import ElectionSettingRepository
from app.schemas.vote import VoteBatchCreate, VoteCreate, VoteUpdate, VoteResponse
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
        session: AsyncSession,
        vote_data: VoteCreate,
        user_id: str,
    ) -> VoteResponse:
        """Create a new vote by sending a transaction to the blockchain."""
        setting_repo = ElectionSettingRepository(session)
        setting = await setting_repo.read_one(
            condition=ElectionSetting.election_id == vote_data.election_id
        )

        if setting and setting.anonymous:
            if not vote_data.anonymous_token:
                raise ValidationError(
                    detail="Anonymous token required for anonymous elections"
                )
            token_repo = AnonymousVoteTokenRepository(session)
            token_record = await token_repo.get_by_token(vote_data.anonymous_token)
            if not token_record:
                raise ValidationError(detail="Invalid anonymous token")
            if token_record.user_id != user_id:
                raise ValidationError(detail="Token does not belong to current user")
            if token_record.election_id != vote_data.election_id:
                raise ValidationError(detail="Token is for a different election")
            if token_record.used_at and not setting.allow_revoting:
                raise ValidationError(detail="Token already used (duplicate vote detected)")
            voter_id = token_record.token
            token_record.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await session.commit()
        else:
            voter_id = user_id

        result = await create_transaction(
            election_id=vote_data.election_id,
            voter_id=voter_id,
            candidate_id=vote_data.candidate_id,
        )
        return VoteResponse(
            id=result.get("transaction_id"),
            election_id=vote_data.election_id,
            voter_id=voter_id,
            candidate_id=vote_data.candidate_id,
            created_at=result.get("created_at"),
        )

    @staticmethod
    async def create_votes_batch(
        session: AsyncSession,
        batch_data: VoteBatchCreate,
        user_id: str,
    ) -> list[VoteResponse]:
        """Create multiple votes at once. For anonymous, token is marked used after all votes."""
        setting_repo = ElectionSettingRepository(session)
        setting = await setting_repo.read_one(
            condition=ElectionSetting.election_id == batch_data.election_id
        )

        voter_id = user_id
        token_record = None

        if setting and setting.anonymous:
            if not batch_data.anonymous_token:
                raise ValidationError(
                    detail="Anonymous token required for anonymous elections"
                )
            token_repo = AnonymousVoteTokenRepository(session)
            token_record = await token_repo.get_by_token(batch_data.anonymous_token)
            if not token_record:
                raise ValidationError(detail="Invalid anonymous token")
            if token_record.user_id != user_id:
                raise ValidationError(detail="Token does not belong to current user")
            if token_record.election_id != batch_data.election_id:
                raise ValidationError(detail="Token is for a different election")
            if token_record.used_at and not setting.allow_revoting:
                raise ValidationError(detail="Token already used (duplicate vote detected)")
            voter_id = token_record.token

        results = []
        for candidate_id in batch_data.candidate_ids:
            result = await create_transaction(
                election_id=batch_data.election_id,
                voter_id=voter_id,
                candidate_id=candidate_id,
            )
            results.append(
                VoteResponse(
                    id=result.get("transaction_id"),
                    election_id=batch_data.election_id,
                    voter_id=voter_id,
                    candidate_id=candidate_id,
                    created_at=result.get("created_at"),
                )
            )

        if token_record:
            token_record.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await session.commit()

        return results

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

    @staticmethod
    async def has_user_voted_anonymous(
        session: AsyncSession, election_id: str, user_id: str
    ) -> bool:
        """Check if user has voted in an anonymous election (by used token)."""
        token_repo = AnonymousVoteTokenRepository(session)
        record = await token_repo.get_by_user_and_election(user_id, election_id)
        return record is not None and record.used_at is not None


vote_service = VoteService()
