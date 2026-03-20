from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from node.models.block import Block
from node.models.transaction import Transaction
from node.repositories.base_repository import BaseRepository


class BlockRepository(BaseRepository):
    """Repository for ``Block`` with chain ordering and transaction joins."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Block, session=session, log_data_name="Block")

    async def get_transaction_ids_in_chain(self, tx_ids: list[str]) -> set[str]:
        """Returns IDs that already appear in any block's transactions.

        Args:
            tx_ids: Candidate transaction UUID strings.

        Returns:
            set[str]: Subset of ``tx_ids`` present on the chain.

        """
        if not tx_ids:
            return set()
        result = await self.session.execute(
            select(Transaction.id).select_from(Block).join(Transaction).where(Transaction.id.in_(tx_ids))
        )
        return set(result.scalars().all())

    async def get_chain_ordered(self) -> list[Block]:
        """Loads the full chain ordered by ``index`` ascending with transactions eager-loaded.

        Returns:
            list[Block]: All blocks in chain order.

        """
        result = await self.session.execute(
            select(Block)
            .options(selectinload(Block.transactions))
            .order_by(Block.index.asc())
        )
        return list(result.scalars().all())

    async def get_last_block(self) -> Block | None:
        """Returns the block with the greatest ``index``.

        Returns:
            Block | None: Tip of the chain, or None if empty.

        """
        result = await self.session.execute(
            select(Block)
            .options(selectinload(Block.transactions))
            .order_by(Block.index.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
