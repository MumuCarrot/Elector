from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_profile import UserProfile
from app.repository.base_repository import BaseRepository


class UserProfileRepository(BaseRepository):
    """Data access for ``UserProfile`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Args:
            session: Async SQLAlchemy session for this unit of work.

        """
        super().__init__(
            model=UserProfile, session=session, log_data_name="UserProfile"
        )
