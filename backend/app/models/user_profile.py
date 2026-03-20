from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(IdMixin, Base):
    """Extended attributes for a user (1:1 via ``user_id``)."""

    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"