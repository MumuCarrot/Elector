from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from node.models.transaction import Transaction
from node.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for ``Transaction`` with election/voter query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            model=Transaction, session=session, log_data_name="Transaction"
        )

    async def get_by_election_id(self, election_id: str) -> list[Transaction]:
        """Lists transactions for an election, oldest first.

        Args:
            election_id: Election identifier.

        Returns:
            list[Transaction]: Matching votes.

        """
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.election_id == election_id)
            .order_by(Transaction.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_voter_id(self, voter_id: str) -> list[Transaction]:
        """Lists transactions for a voter, oldest first.

        Args:
            voter_id: Voter (user) identifier.

        Returns:
            list[Transaction]: Matching votes.

        """
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.voter_id == voter_id)
            .order_by(Transaction.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_election_and_voter(
        self, election_id: str, voter_id: str
    ) -> Transaction | None:
        """Returns the earliest transaction for a voter in an election.

        Args:
            election_id: Election identifier.
            voter_id: Voter identifier.

        Returns:
            Transaction | None: First vote by ``created_at``, or None.

        """
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
