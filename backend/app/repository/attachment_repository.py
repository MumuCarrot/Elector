from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment
from app.repository.base_repository import BaseRepository


class AttachmentRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Attachment, session=session, log_data_name="Attachment")