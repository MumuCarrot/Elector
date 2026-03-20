from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.user_role_link import UserRoleLink


class UserRole(IdMixin, Base):
    """Named role label (e.g. admin) for RBAC."""

    __tablename__ = "user_roles"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # Relationships
    role_links: Mapped[list["UserRoleLink"]] = relationship("UserRoleLink", back_populates="role")

    def __repr__(self):
        return f"<UserRole(id={self.id}, name='{self.name}')>"