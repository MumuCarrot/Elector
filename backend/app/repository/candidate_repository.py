from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidates import Candidate
from app.repository.base_repository import BaseRepository


class CandidateRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Candidate, session=session, log_data_name="Candidate")

