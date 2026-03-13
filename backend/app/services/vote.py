from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.exceptions.user import PermissionDeniedError, VoteNotFoundError
from app.models.user import User
from app.models.vote import Vote
from app.repository.vote_repository import VoteRepository
from app.schemas.vote import VoteCreate, VoteUpdate, VoteResponse

logger = get_logger("vote_service")


class VoteService:
    """Service for vote CRUD operations."""

    @staticmethod
    async def create_vote(
        session: AsyncSession, vote_data: VoteCreate, current_user: User
    ) -> VoteResponse:
        """Create a new vote."""
        logger.info(
            f"Creating vote for election {vote_data.election_id} by user {current_user.id}"
        )

        repository = VoteRepository(session)

        new_vote = Vote(
            election_id=vote_data.election_id,
            voter_id=current_user.id,
            candidate_id=vote_data.candidate_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        created_vote = await repository.create(new_vote)
        logger.info(f"Vote created successfully with id: {created_vote.id}")

        return VoteResponse.model_validate(created_vote)

    @staticmethod
    async def get_vote_by_id(
        session: AsyncSession, vote_id: str
    ) -> Optional[VoteResponse]:
        """Get vote by ID."""
        logger.info(f"Getting vote by id: {vote_id}")

        repository = VoteRepository(session)
        vote = await repository.read_one(condition=Vote.id == vote_id)

        if not vote:
            logger.warning(f"Vote with id {vote_id} not found")
            return None

        return VoteResponse.model_validate(vote)

    @staticmethod
    async def get_votes_by_election(
        session: AsyncSession, election_id: str
    ) -> list[VoteResponse]:
        """Get all votes for a specific election."""
        logger.info(f"Getting votes for election: {election_id}")

        repository = VoteRepository(session)
        votes = await repository.read_many(condition=Vote.election_id == election_id)

        if not votes:
            return []

        return [VoteResponse.model_validate(vote) for vote in votes]

    @staticmethod
    async def get_votes_by_user(
        session: AsyncSession, user_id: str
    ) -> list[VoteResponse]:
        """Get all votes by a specific user."""
        logger.info(f"Getting votes for user: {user_id}")

        repository = VoteRepository(session)
        votes = await repository.read_many(condition=Vote.voter_id == user_id)

        if not votes:
            return []

        return [VoteResponse.model_validate(vote) for vote in votes]

    @staticmethod
    async def get_user_vote_for_election(
        session: AsyncSession, election_id: str, user_id: str
    ) -> Optional[VoteResponse]:
        """Get user's vote for a specific election."""
        logger.debug(
            f"Getting vote for election {election_id} by user {user_id}"
        )

        repository = VoteRepository(session)
        vote = await repository.read_one(
            condition=(
                (Vote.election_id == election_id) & (Vote.voter_id == user_id)
            )
        )

        if not vote:
            return None

        return VoteResponse.model_validate(vote)

    @staticmethod
    async def update_vote(
        session: AsyncSession,
        vote_id: str,
        vote_data: VoteUpdate,
        current_user: User,
    ) -> VoteResponse:
        """Update vote information."""
        logger.info(f"Updating vote with id: {vote_id}")

        repository = VoteRepository(session)
        vote = await repository.read_one(condition=Vote.id == vote_id)

        if not vote:
            logger.warning(f"Vote with id {vote_id} not found")
            raise VoteNotFoundError(f"Vote with id {vote_id} not found")

        if vote.voter_id != current_user.id:
            logger.warning(
                f"User {current_user.id} attempted to update vote {vote_id} owned by {vote.voter_id}"
            )
            raise PermissionDeniedError(
                "You don't have permission to update this vote"
            )

        update_dict = vote_data.model_dump(exclude_unset=True)

        if "voter_id" in update_dict:
            logger.warning("Attempt to change voter_id in vote update")
            update_dict.pop("voter_id")

        updated_vote = await repository.update(
            data=update_dict, condition=Vote.id == vote_id
        )

        logger.info(f"Vote with id {vote_id} updated successfully")

        return VoteResponse.model_validate(updated_vote)

    @staticmethod
    async def delete_vote(
        session: AsyncSession, vote_id: str, current_user: User
    ) -> bool:
        """Delete vote by ID."""
        logger.info(f"Deleting vote with id: {vote_id}")

        repository = VoteRepository(session)
        vote = await repository.read_one(condition=Vote.id == vote_id)

        if not vote:
            logger.warning(f"Vote with id {vote_id} not found for deletion")
            raise VoteNotFoundError(f"Vote with id {vote_id} not found")

        if vote.voter_id != current_user.id:
            logger.warning(
                f"User {current_user.id} attempted to delete vote {vote_id} owned by {vote.voter_id}"
            )
            raise PermissionDeniedError(
                "You don't have permission to delete this vote"
            )

        deleted = await repository.delete(condition=Vote.id == vote_id)

        if not deleted:
            logger.warning(f"Failed to delete vote with id {vote_id}")
            raise VoteNotFoundError(f"Vote with id {vote_id} not found")

        logger.info(f"Vote with id {vote_id} deleted successfully")
        return True

    @staticmethod
    async def get_all_votes(
        session: AsyncSession, page: int = 1, page_size: int = 10
    ) -> list[VoteResponse]:
        """Get all votes with pagination."""
        logger.info(f"Getting all votes - page: {page}, page_size: {page_size}")

        repository = VoteRepository(session)
        votes = await repository.read_paginated(
            condition=True, page=page, page_size=page_size
        )

        if not votes:
            return []

        return [VoteResponse.model_validate(vote) for vote in votes]


vote_service = VoteService()
