from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile
    from app.models.user_role_link import UserRoleLink
    from app.models.election_access import ElectionAccess
    from app.models.attachment import Attachment


class User(IdMixin, Base):
    """Registered account with hashed password and optional profile/roles."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)

    __table_args__ = (
        Index('idx_user_phone', 'phone'),
        Index('idx_user_created_at', 'created_at'),
    )

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False)
    role_links: Mapped[list["UserRoleLink"]] = relationship("UserRoleLink", back_populates="user")
    election_accesses: Mapped[list["ElectionAccess"]] = relationship("ElectionAccess", back_populates="user")
    attachments: Mapped[list["Attachment"]] = relationship("Attachment", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"