from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Data access for ``User`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Args:
            session: Async SQLAlchemy session for this unit of work.

        """
        super().__init__(model=User, session=session, log_data_name="User")
