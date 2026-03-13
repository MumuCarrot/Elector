from typing import Any, Type

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from node.db.database import Base


class BaseRepository:
    """
    Base repository class for common database operations.
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

    async def create(
        self,
        data: Any,
    ) -> Any:
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

    async def update(
        self,
        data: Any,
        condition: Any = None,
    ) -> Any:
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

    async def read_one(
        self,
        condition: Any = False,
        options: Any = None,
    ) -> Any:
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

    async def read_many(
        self,
        condition: Any = False,
    ) -> Any:
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
        try:
            return await self.read_one(condition=condition) is not None
        except Exception as e:
            raise

    async def contains_many(self, condition: Any = False) -> list[Any]:
        try:
            return await self.read_many(condition=condition) is not None
        except Exception as e:
            raise

    async def count(self, condition: Any = True) -> int:
        try:
            result = await self.session.execute(
                select(func.count()).select_from(self.model).where(condition)
            )
            return result.scalar() or 0
        except Exception as e:
            raise

            