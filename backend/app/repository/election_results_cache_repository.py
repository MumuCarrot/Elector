from sqlalchemy.ext.asyncio import AsyncSession

from app.models.election_results_cache import ElectionResultsCache
from app.repository.base_repository import BaseRepository


class ElectionResultsCacheRepository(BaseRepository):
    """Data access for ``ElectionResultsCache`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Args:
            session: Async SQLAlchemy session for this unit of work.

        """
        super().__init__(
            model=ElectionResultsCache,
            session=session,
            log_data_name="ElectionResultsCache",
        )
