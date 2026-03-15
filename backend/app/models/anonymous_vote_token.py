from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.id_mixin import IdMixin

if TYPE_CHECKING:
    from app.models.election import Election
    from app.models.user import User


class AnonymousVoteToken(IdMixin, Base):
    """One-time token for anonymous voting. One token per user per election."""

    __tablename__ = "anonymous_vote_tokens"
    __table_args__ = (
        Index("idx_anon_token_user_election", "user_id", "election_id", unique=True),
        Index("idx_anon_token_token", "token", unique=True),
        Index("idx_anon_token_election", "election_id"),
    )

    election_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("elections.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
