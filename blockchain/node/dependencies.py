from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from node.db.database import async_session_maker
from node.services.node import Node


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


def get_blockchain(request: Request, session: AsyncSession = Depends(get_session)) -> Node:
    """Node is created at app startup (lifespan), stored in app.state."""
    node = request.app.state.blockchain_node
    node.session = session
    return node