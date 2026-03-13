from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_profile import UserProfile
from app.repository.base_repository import BaseRepository


class UserProfileRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=UserProfile, session=session, log_data_name="UserProfile")

