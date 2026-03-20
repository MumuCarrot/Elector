from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.election import Election


class ElectionResultsCache(IdMixin, Base):
    """Optional JSON snapshot of computed results per election."""

    __tablename__ = "election_results_cache"

    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id"),
        unique=True,
        nullable=False
    )
    results_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    __table_args__ = (
        Index('idx_election_results_cache_updated_at', 'updated_at'),
    )

    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="results_cache")

    def __repr__(self):
        return f"<ElectionResultsCache(id={self.id}, election_id={self.election_id})>"