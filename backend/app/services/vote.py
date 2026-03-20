from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.exceptions.user import ValidationError
from app.models.election_setting import ElectionSetting
from app.repository.anonymous_vote_token_repository import AnonymousVoteTokenRepository
from app.repository.election_setting_repository import ElectionSettingRepository
from app.schemas.vote import VoteBatchCreate, VoteCreate, VoteResponse
from app.services.blockchain_client import (
    create_transaction,
    get_votes_by_election,
    get_votes_by_user,
    get_user_vote_for_election,
)

logger = get_logger("vote_service")


class VoteService:
    """Submits votes to the blockchain and reads tallies via HTTP addon API."""

    @staticmethod
    async def create_vote(
        session: AsyncSession,
        vote_data: VoteCreate,
        user_id: str,
    ) -> VoteResponse:
        """Creates one on-chain vote; maps anonymous tokens to opaque voter ids.

        Args:
            session: DB session (token state updates).
            vote_data: Election, candidate, optional anonymous token.
            user_id: Authenticated user id.

        Returns:
            VoteResponse: Echo from blockchain create call.

        Raises:
            ValidationError: Anonymous rules violated or bad token.

        """
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
        """Submits multiple candidate choices; marks anonymous token used once at end.

        Args:
            session: DB session.
            batch_data: Election id, candidate id list, optional token.
            user_id: Authenticated user id.

        Returns:
            list[VoteResponse]: One entry per successful blockchain transaction.

        Raises:
            ValidationError: Same anonymous checks as ``create_vote``.

        """
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
        """Aggregates candidate vote counts from blockchain read API.

        Args:
            election_id: Election id.

        Returns:
            dict: Candidate id -> count map.

        """
        votes = await get_votes_by_election(election_id)
        results = {}
        for vote in votes.get("votes", []):
            candidate_id = vote.get("candidate_id")
            results[candidate_id] = results.get(candidate_id, 0) + 1
        return results

    @staticmethod
    async def get_votes_by_user(
        user_id: str,
    ) -> list[VoteResponse]:
        """Lists votes where ``voter_id`` equals the given user (or token id).

        Args:
            user_id: Voter identifier as stored on chain.

        Returns:
            list[VoteResponse]: Parsed transactions.

        """
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
        """Fetches a single vote row for user+election from blockchain.

        Args:
            election_id: Election id.
            user_id: Voter id on chain (real user id for non-anonymous).

        Returns:
            VoteResponse | None: None if HTTP 404 from node.

        """
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
        """True if an anonymous token row exists and ``used_at`` is set.

        Args:
            session: DB session.
            election_id: Election id.
            user_id: Real user id (not token string).

        Returns:
            bool: Participation flag for anonymous flows.

        """
        token_repo = AnonymousVoteTokenRepository(session)
        record = await token_repo.get_by_user_and_election(user_id, election_id)
        return record is not None and record.used_at is not None


vote_service = VoteService()
