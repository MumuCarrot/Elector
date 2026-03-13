from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.election import Election
    from app.models.user import User
    from app.models.candidates import Candidate


class Vote(IdMixin, Base):
    __tablename__ = "votes"

    election_id: Mapped[str] = mapped_column(String(36), ForeignKey("elections.id"), nullable=False)
    voter_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id"), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    __table_args__ = (
        Index('idx_vote_election_id', 'election_id'),
        Index('idx_vote_voter_id', 'voter_id'),
        Index('idx_vote_candidate_id', 'candidate_id'),
        Index('idx_vote_created_at', 'created_at'),
        Index('idx_vote_election_voter', 'election_id', 'voter_id'),
    )

    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="votes")
    voter: Mapped["User"] = relationship("User", back_populates="votes", foreign_keys=[voter_id])
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="votes")

    def __repr__(self):
        return f"<Vote(id={self.id}, election_id={self.election_id}, voter_id={self.voter_id}, candidate_id={self.candidate_id})>"