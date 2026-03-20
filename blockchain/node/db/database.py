from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from node.core.settings import settings

Base = declarative_base()

engine = create_async_engine(
    str(settings.database_settings.DATABASE_URL),
    echo=settings.database_settings.SQL_ECHO,
)

async_session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
