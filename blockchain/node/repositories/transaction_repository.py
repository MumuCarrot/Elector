from sqlalchemy.ext.asyncio import AsyncSession

from node.models.transaction import Transaction
from node.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            model=Transaction, session=session, log_data_name="Transaction"
        )