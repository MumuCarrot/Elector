from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.election import Election
    from app.models.candidates import Candidate


class Attachment(IdMixin, Base):
    """File URL linked optionally to user, election, or candidate."""

    __tablename__ = "attachments"

    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    election_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("elections.id"), nullable=True)
    candidate_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("candidates.id"), nullable=True)
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    __table_args__ = (
        Index('idx_attachment_user_id', 'user_id'),
        Index('idx_attachment_election_id', 'election_id'),
        Index('idx_attachment_candidate_id', 'candidate_id'),
        Index('idx_attachment_uploaded_at', 'uploaded_at'),
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="attachments")
    election: Mapped[Optional["Election"]] = relationship("Election", back_populates="attachments")
    candidate: Mapped[Optional["Candidate"]] = relationship("Candidate", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment(id={self.id}, file_url='{self.file_url}')>"