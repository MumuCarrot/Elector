from app.db.database import async_session_maker


async def get_db():
    """FastAPI dependency yielding an async SQLAlchemy session per request.

    Yields:
        AsyncSession: Database session; closed when the request completes.

    """
    async with async_session_maker() as session:
        yield session
