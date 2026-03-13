from app.db.database import async_session_maker


async def get_db():
    """
    Context manager for using database session in services.
    """
    async with async_session_maker() as session:
        yield session