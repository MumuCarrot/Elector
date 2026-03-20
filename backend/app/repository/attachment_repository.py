from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment
from app.repository.base_repository import BaseRepository


class AttachmentRepository(BaseRepository):
    """Data access for ``Attachment`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Args:
            session: Async SQLAlchemy session for this unit of work.

        """
        super().__init__(
            model=Attachment, session=session, log_data_name="Attachment"
        )
