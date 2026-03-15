from typing import TYPE_CHECKING

from sqlalchemy import Integer, Boolean, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.election import Election


class ElectionSetting(IdMixin, Base):
    __tablename__ = "election_settings"

    election_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("elections.id"),
        unique=True,
        nullable=False
    )
    allow_revoting: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_votes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    require_auth: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    election: Mapped["Election"] = relationship("Election", back_populates="settings")

    def __repr__(self):
        return f"<ElectionSetting(id={self.id}, election_id={self.election_id})>"