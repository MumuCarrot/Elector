from sqlalchemy.ext.asyncio import AsyncSession

from app.models.election_results_cache import ElectionResultsCache
from app.repository.base_repository import BaseRepository


class ElectionResultsCacheRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            model=ElectionResultsCache,
            session=session,
            log_data_name="ElectionResultsCache",
        )

