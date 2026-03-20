from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from node.db.database import async_session_maker
from node.services.node import Node


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields an async SQLAlchemy session for the request scope.

    Yields:
        AsyncSession: Database session; closed after the request completes.

    """
    async with async_session_maker() as session:
        yield session


def get_blockchain(request: Request, session: AsyncSession = Depends(get_session)) -> Node:
    """Returns the Node instance created in app lifespan, bound to the request session.

    The node is stored on ``request.app.state.blockchain_node`` at startup. The request
    ``session`` is assigned so route handlers can use ``blockchain.session`` without
    passing the session separately where the pattern is used.

    Args:
        request: Incoming HTTP request (provides ``app.state``).
        session: Async database session from ``get_session``.

    Returns:
        Node: The singleton blockchain node for this process.

    """
    node = request.app.state.blockchain_node
    node.session = session
    return node
