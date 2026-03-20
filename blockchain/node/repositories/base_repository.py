from typing import Any, Type

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from node.db.database import Base


class BaseRepository:
    """CRUD-style helpers around a single SQLAlchemy model and ``AsyncSession``.

    Attributes:
        model: Declarative model class.
        session: Async session used for all operations.
        log_data_name: Human-readable name for error messages.

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
        """Inserts one row and refreshes the instance.

        Args:
            data: ORM instance to persist.

        Returns:
            The same instance after commit and refresh.

        Raises:
            ValueError: On unique/integrity violations (after rollback).
            Exception: Other errors propagate after rollback.

        """
        try:
            self.session.add(data)

            await self.session.commit()
            await self.session.refresh(data)

            return data

        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(str(e))

        except Exception as e:
            await self.session.rollback()
            raise

    async def create_many(self, data: list[Any]) -> list[Any]:
        """Inserts multiple rows in one transaction.

        Args:
            data: List of ORM instances.

        Returns:
            The same list after commit (refresh behavior depends on SQLAlchemy).

        Raises:
            ValueError: On integrity errors.
            Exception: Other errors after rollback.

        """
        try:
            self.session.add_all(data)

            await self.session.commit()
            await self.session.refresh(data)

            return data

        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(str(e))

        except Exception as e:
            await self.session.rollback()
            raise

    async def update(self, data: Any, condition: Any = None) -> Any:
        """Updates a row by tracked instance or by ``condition`` + payload.

        Args:
            data: Tracked ORM instance, dict of fields, or ORM instance with values.
            condition: SQLAlchemy filter when ``data`` is not a tracked instance.

        Returns:
            Updated ORM instance.

        Raises:
            ValueError: If condition is missing, row not found, or instance not tracked.

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
            raise

    async def delete(self, condition: Any = False) -> bool:
        """Deletes the first row matching ``condition``.

        Args:
            condition: SQLAlchemy boolean expression.

        Returns:
            bool: True if a row was deleted.

        """
        try:
            result = await self.session.execute(select(self.model).where(condition))
            data = result.scalar_one_or_none()

            if not data:
                return False

            await self.session.delete(data)
            await self.session.commit()

            return True

        except Exception as e:
            await self.session.rollback()
            raise

    async def delete_many(self, condition: Any = False) -> list[Any]:
        """Deletes all rows matching ``condition``.

        Args:
            condition: SQLAlchemy boolean expression.

        Returns:
            list: Deleted instances (empty if none matched).

        """
        try:
            result = await self.session.execute(select(self.model).where(condition))
            data = result.scalars().all()

            if not data:
                return []

            for item in data:
                await self.session.delete(item)

            await self.session.commit()

            return data

        except Exception as e:
            await self.session.rollback()
            raise

    async def read_one(self, condition: Any = False, options: Any = None) -> Any:
        """Returns one row or None.

        Args:
            condition: SQLAlchemy filter.
            options: Optional list of loader options for ``select``.

        Returns:
            Model instance or None.

        """
        try:
            result = await self.session.execute(
                select(self.model).where(condition).options(*(options or []))
            )
            data = result.scalar_one_or_none()

            if not data:
                return None

            return data

        except Exception as e:
            raise

    async def read_many(self, condition: Any = False) -> Any:
        """Returns all rows matching ``condition``.

        Args:
            condition: SQLAlchemy filter.

        Returns:
            list: Matching rows, or empty list.

        """
        try:
            result = await self.session.execute(select(self.model).where(condition))
            data = result.scalars().all()

            if not data:
                return []

            return data

        except Exception as e:
            raise

    async def read_paginated(
        self,
        condition: Any = True,
        page: int = 1,
        page_size: int = 0,
    ) -> Any:
        """Returns a page of rows using offset/limit.

        Args:
            condition: SQLAlchemy filter; default matches all.
            page: 1-based page index.
            page_size: Page size (0 yields offset logic with limit 0).

        Returns:
            list: Rows for the page.

        """
        try:
            offset = (page - 1) * page_size
            result = await self.session.execute(
                select(self.model).where(condition).offset(offset).limit(page_size)
            )
            data = result.scalars().all()

            if not data:
                return []

            return data

        except Exception as e:
            raise

    async def contains(self, condition: Any = False) -> bool:
        """Returns whether any row matches ``condition``."""

        try:
            return await self.read_one(condition=condition) is not None
        except Exception as e:
            raise

    async def contains_many(self, condition: Any = False) -> list[Any]:
        """Legacy helper: compares ``read_many`` result to None (empty list is still not None).

        Returns:
            bool: True when ``read_many`` does not return None.

        """

        try:
            return await self.read_many(condition=condition) is not None
        except Exception as e:
            raise

    async def count(self, condition: Any = True) -> int:
        """Counts rows matching ``condition``.

        Args:
            condition: SQLAlchemy filter; default counts all rows.

        Returns:
            int: Row count.

        """
        try:
            result = await self.session.execute(
                select(func.count()).select_from(self.model).where(condition)
            )
            return result.scalar() or 0
        except Exception as e:
            raise
