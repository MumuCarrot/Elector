from sqlalchemy.ext.asyncio import AsyncSession

from app.models.election_setting import ElectionSetting
from app.repository.base_repository import BaseRepository


class ElectionSettingRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ElectionSetting, session=session, log_data_name="ElectionSetting")

