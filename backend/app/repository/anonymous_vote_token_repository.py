from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anonymous_vote_token import AnonymousVoteToken
from app.repository.base_repository import BaseRepository


class AnonymousVoteTokenRepository(BaseRepository):
    """Data access for one-time anonymous voting tokens."""

    def __init__(self, session: AsyncSession) -> None:
        """Args:
            session: Async SQLAlchemy session for this unit of work.

        """
        super().__init__(
            model=AnonymousVoteToken,
            session=session,
            log_data_name="AnonymousVoteToken",
        )

    async def get_by_user_and_election(
        self, user_id: str, election_id: str
    ) -> AnonymousVoteToken | None:
        """Returns the token row for a user+election pair if any.

        Args:
            user_id: Real user id.
            election_id: Election id.

        Returns:
            AnonymousVoteToken | None: Matching row or None.

        """
        result = await self.session.execute(
            select(AnonymousVoteToken).where(
                AnonymousVoteToken.user_id == user_id,
                AnonymousVoteToken.election_id == election_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> AnonymousVoteToken | None:
        """Looks up a row by opaque token string.

        Args:
            token: URL-safe token issued to the client.

        Returns:
            AnonymousVoteToken | None: Row or None.

        """
        result = await self.session.execute(
            select(AnonymousVoteToken).where(AnonymousVoteToken.token == token)
        )
        return result.scalar_one_or_none()
