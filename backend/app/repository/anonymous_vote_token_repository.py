from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.anonymous_vote_token import AnonymousVoteToken
from app.repository.base_repository import BaseRepository


class AnonymousVoteTokenRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            model=AnonymousVoteToken,
            session=session,
            log_data_name="AnonymousVoteToken",
        )

    async def get_by_user_and_election(
        self, user_id: str, election_id: str
    ) -> AnonymousVoteToken | None:
        result = await self.session.execute(
            select(AnonymousVoteToken).where(
                AnonymousVoteToken.user_id == user_id,
                AnonymousVoteToken.election_id == election_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> AnonymousVoteToken | None:
        result = await self.session.execute(
            select(AnonymousVoteToken).where(AnonymousVoteToken.token == token)
        )
        return result.scalar_one_or_none()
