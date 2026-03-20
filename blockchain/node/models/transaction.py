from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from node.db.database import Base
from node.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from node.models.block import Block


class Transaction(IdMixin, Base):
    """A single vote linking election, voter, and candidate to a block.

    Attributes:
        block_id: Foreign key to the containing block.
        election_id: Election identifier from the application domain.
        voter_id: Voter (user) identifier.
        candidate_id: Chosen candidate identifier.
        created_at: Optional creation timestamp.
        block: Parent block relationship.

    """

    __tablename__ = "transactions"
    block_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blockchain_blocks.id"),
        nullable=False,
    )
    election_id: Mapped[str] = mapped_column(String, nullable=False)
    voter_id: Mapped[str] = mapped_column(String, nullable=False)
    candidate_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    __table_args__ = (
        Index("idx_bc_tx_block_id", "block_id"),
        Index("idx_bc_tx_election_id", "election_id"),
        Index("idx_bc_tx_voter_id", "voter_id"),
        Index("idx_bc_tx_candidate_id", "candidate_id"),
        Index("idx_bc_tx_created_at", "created_at"),
    )
    block: Mapped["Block"] = relationship(
        "Block", back_populates="transactions"
    )
