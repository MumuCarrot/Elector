from sqlalchemy.ext.asyncio import AsyncSession

from app.models.election import Election
from app.repository.base_repository import BaseRepository


class ElectionRepository(BaseRepository):
    """Data access for ``Election`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Args:
            session: Async SQLAlchemy session for this unit of work.

        """
        super().__init__(model=Election, session=session, log_data_name="Election")
