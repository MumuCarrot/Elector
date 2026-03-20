from sqlalchemy.ext.asyncio import AsyncSession

from app.models.election_setting import ElectionSetting
from app.repository.base_repository import BaseRepository


class ElectionSettingRepository(BaseRepository):
    """Data access for ``ElectionSetting`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Args:
            session: Async SQLAlchemy session for this unit of work.

        """
        super().__init__(
            model=ElectionSetting,
            session=session,
            log_data_name="ElectionSetting",
        )
