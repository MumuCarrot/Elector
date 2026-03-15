from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.election import Election
    from app.models.attachment import Attachment


class Candidate(IdMixin, Base):
    __tablename__ = "candidates"

    election_id: Mapped[str] = mapped_column(String(36), ForeignKey("elections.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index('idx_candidate_election_id', 'election_id'),
    )

    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="candidates")
    attachments: Mapped[list["Attachment"]] = relationship("Attachment", back_populates="candidate")

    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.name}', election_id={self.election_id})>"