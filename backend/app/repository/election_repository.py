from sqlalchemy.ext.asyncio import AsyncSession

from app.models.election import Election
from app.repository.base_repository import BaseRepository


class ElectionRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Election, session=session, log_data_name="Election")

