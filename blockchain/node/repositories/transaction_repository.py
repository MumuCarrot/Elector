from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from node.models.transaction import Transaction
from node.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            model=Transaction, session=session, log_data_name="Transaction"
        )


    async def get_by_election_id(self, election_id: str) -> list[Transaction]:
        """Get all transactions (votes) for an election, ordered by created_at."""

        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.election_id == election_id)
            .order_by(Transaction.created_at.asc())
        )
        return list(result.scalars().all())


    async def get_by_voter_id(self, voter_id: str) -> list[Transaction]:
        """Get all transactions (votes) by a voter, ordered by created_at."""

        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.voter_id == voter_id)
            .order_by(Transaction.created_at.asc())
        )
        return list(result.scalars().all())


    async def get_by_election_and_voter(
        self, election_id: str, voter_id: str
    ) -> Transaction | None:
        """Get a voter's transaction for a specific election (first by created_at)."""
        
        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.election_id == election_id,
                Transaction.voter_id == voter_id,
            )
            .order_by(Transaction.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()