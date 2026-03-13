from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from node.db.database import Base
from node.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from node.models.transaction import Transaction

class Block(IdMixin, Base):
    __tablename__ = "blockchain_blocks"
    index: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    nonce: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    __table_args__ = (
        Index("idx_blockchain_block_index", "index"),
        Index("idx_blockchain_block_hash", "hash"),
        Index("idx_blockchain_block_created_at", "created_at"),
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="block",
        cascade="all, delete-orphan",
    )