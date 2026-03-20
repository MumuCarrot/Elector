from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.user_role import UserRole


class UserRoleLink(IdMixin, Base):
    """Associates a user with a ``UserRole``."""

    __tablename__ = "user_role_links"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user_roles.id"),
        nullable=False
    )

    __table_args__ = (
        Index('idx_user_role_link_user_id', 'user_id'),
        Index('idx_user_role_link_role_id', 'role_id'),
        Index('idx_user_role_link_user_role', 'user_id', 'role_id'),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="role_links")
    role: Mapped["UserRole"] = relationship("UserRole", back_populates="role_links")

    def __repr__(self):
        return f"<UserRoleLink(id={self.id}, user_id={self.user_id}, role_id={self.role_id})>"