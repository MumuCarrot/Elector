from typing import Any, Type

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.db.database import Base

logger = get_logger("base_repo")


class BaseRepository:
    """Async CRUD helpers for a single SQLAlchemy declarative model.

    Attributes:
        model: ORM model class bound to this repository.
        session: Async session used for all queries and commits.
        log_data_name: Label used in log messages for this entity type.

    """

    def __init__(
        self,
        model: Type[Base],
        session: AsyncSession,
        log_data_name: str = "Entity",
    ):
        self.model = model
        self.session = session
        self.log_data_name = log_data_name

    async def create(self, data: Any) -> Any:
        """Persists a new ORM instance.

        Args:
            data: Model instance to insert.

        Returns:
            The refreshed instance after commit.

        Raises:
            ValueError: On integrity constraint violations.
            Exception: Other errors are logged and re-raised after rollback.

        """
        try:
            self.session.add(data)

            await self.session.commit()
            await self.session.refresh(data)

            return data

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Database integrity error creating {self.log_data_name}: {str(e)}"
            )
            raise ValueError(str(e))

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating {self.log_data_name}: {str(e)}")
            raise

    async def update(self, data: Any, condition: Any = None) -> Any:
        """Updates a row by tracked instance or by filter plus dict/model payload.

        Args:
            data: Tracked instance, dict of fields, or model with new values.
            condition: SQLAlchemy filter when ``data`` is not a tracked instance.

        Returns:
            Updated ORM instance.

        Raises:
            ValueError: Missing condition, row not found, or instance not tracked.

        """
        try:
            if isinstance(data, self.model) and condition is None:
                try:
                    await self.session.commit()
                    await self.session.refresh(data)
                    return data
                except Exception:
                    raise ValueError(
                        f"{self.log_data_name} instance is not tracked by the session. "
                        "Provide a condition to find the record."
                    )

            if condition is None:
                raise ValueError(
                    "Condition is required when data is not a tracked model instance"
                )

            result = await self.session.execute(select(self.model).where(condition))
            existing_data = result.scalar_one_or_none()

            if not existing_data:
                err = f"Attempt to update {self.log_data_name} failed: not found."
                logger.warning(err)
                raise ValueError(err)

            if isinstance(data, dict):
                for key, value in data.items():
                    if hasattr(existing_data, key) and value is not None:
                        setattr(existing_data, key, value)
            elif isinstance(data, self.model):
                for column in self.model.__table__.columns:
                    attr_name = column.name
                    new_value = getattr(data, attr_name, None)
                    if new_value is not None:
                        setattr(existing_data, attr_name, new_value)
            else:
                for attr_name in dir(data):
                    if not attr_name.startswith("_"):
                        new_value = getattr(data, attr_name, None)
                        if new_value is not None and hasattr(existing_data, attr_name):
                            setattr(existing_data, attr_name, new_value)

            await self.session.commit()
            await self.session.refresh(existing_data)

            return existing_data

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating {self.log_data_name}: {str(e)}")
            raise

    async def delete(self, condition: Any = False) -> bool:
        """Deletes the first row matching ``condition``.

        Args:
            condition: SQLAlchemy boolean expression.

        Returns:
            True if a row was deleted.

        """
        try:
            result = await self.session.execute(select(self.model).where(condition))
            data = result.scalar_one_or_none()

            if not data:
                logger.warning(f"{self.log_data_name} not found for deletion.")
                return False

            await self.session.delete(data)
            await self.session.commit()

            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting {self.log_data_name}: {str(e)}")
            raise

    async def read_one(self, condition: Any = False, options: Any = None) -> Any:
        """Returns one row or None.

        Args:
            condition: SQLAlchemy filter expression.
            options: Optional sequence of loader options for ``select``.

        Returns:
            Model instance or None.

        """
        try:
            result = await self.session.execute(
                select(self.model).where(condition).options(*(options or []))
            )
            data = result.scalar_one_or_none()

            if not data:
                logger.warning(f"{self.log_data_name} not found.")
                return None

            return data

        except Exception as e:
            logger.error(f"Error reading {self.log_data_name}: {str(e)}")
            raise

    async def read_many(self, condition: Any = False) -> Any:
        """Returns all rows matching ``condition``.

        Args:
            condition: SQLAlchemy filter expression.

        Returns:
            List of instances, or empty list if none match.

        """
        try:
            result = await self.session.execute(select(self.model).where(condition))
            data = result.scalars().all()

            if not data:
                logger.warning(f"{self.log_data_name} not found.")
                return []

            return data

        except Exception as e:
            logger.error(f"Error reading {self.log_data_name}: {str(e)}")
            raise

    async def read_paginated(
        self,
        condition: Any = True,
        page: int = 1,
        page_size: int = 0,
    ) -> Any:
        """Returns a slice of rows using offset/limit pagination.

        Args:
            condition: Filter expression; default includes all rows.
            page: 1-based page index.
            page_size: Maximum rows per page.

        Returns:
            List of instances for the requested page.

        """
        try:
            offset = (page - 1) * page_size
            result = await self.session.execute(
                select(self.model).where(condition).offset(offset).limit(page_size)
            )
            data = result.scalars().all()

            if not data:
                logger.warning(f"{self.log_data_name} not found.")
                return []

            return data

        except Exception as e:
            logger.error(f"Error reading {self.log_data_name}: {str(e)}")
            raise
