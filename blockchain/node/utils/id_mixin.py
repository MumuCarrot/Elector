from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class IdMixin:
    """Adds a string UUID primary key column ``id``."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        unique=True,
    )
