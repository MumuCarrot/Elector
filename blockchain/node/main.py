import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from node.core.settings import settings
from node.logging_config import setup_logging

setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
from node.routers.api_addons import router as api_addons_router
from node.routers.health import router as health_router
from node.routers.blockchain import router as blockchain_router
from node.routers.node import router as node_router
from node.routers.gossip import router as gossip_router
from node.services.node import Node


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create Node at startup and run mining in main event loop (avoids asyncpg issues)."""

    actual_host = os.environ.get("NODE_ACTUAL_HOST", settings.app.APP_HOST)
    actual_port = int(os.environ.get("NODE_ACTUAL_PORT", settings.app.APP_PORT))
    node = Node(host=actual_host, port=actual_port, is_copy=True)
    await node.initialize()
    app.state.blockchain_node = node
    yield
    if node._mining_task and not node._mining_task.done():
        node._mining_task.cancel()
        try:
            await node._mining_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)


app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(blockchain_router, prefix="/blockchain", tags=["blockchain"])
app.include_router(api_addons_router, prefix="/api", tags=["api"])
app.include_router(node_router, prefix="/nodes", tags=["nodes"])
app.include_router(gossip_router, prefix="/gossip", tags=["gossip"])