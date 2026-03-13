from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vote import Vote
from app.repository.base_repository import BaseRepository


class VoteRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Vote, session=session, log_data_name="Vote")

