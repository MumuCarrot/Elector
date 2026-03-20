"""
Test app with in-memory SQLite, no long-running mining, stubbed outbound HTTP.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi import FastAPI


@pytest.fixture(autouse=True)
def stub_outbound_requests(monkeypatch):
    """Avoid real HTTP when gossip/sync runs (empty or non-empty peer lists)."""

    class Resp:
        status_code = 200
        text = ""

        def json(self):
            return {
                "chain": [],
                "length": 0,
                "nodes": [],
                "transactions": [],
                "votes": [],
            }

    def _get(*args, **kwargs):
        return Resp()

    def _post(*args, **kwargs):
        r = Resp()
        r.status_code = 201
        return r

    monkeypatch.setattr("node.services.node.requests.get", _get)
    monkeypatch.setattr("node.services.node.requests.post", _post)


@pytest_asyncio.fixture(autouse=True)
async def sqlite_engine_and_session_maker(monkeypatch):
    from node.db.database import Base
    import node.db.database as db_mod
    import node.dependencies as dep_mod
    import node.services.node as node_mod

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSession = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    monkeypatch.setattr(db_mod, "engine", engine)
    monkeypatch.setattr(db_mod, "async_session_maker", TestSession)
    monkeypatch.setattr(dep_mod, "async_session_maker", TestSession)
    monkeypatch.setattr(node_mod, "async_session_maker", TestSession)

    yield TestSession

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@asynccontextmanager
async def _test_lifespan(app: FastAPI):
    from node.services.node import Node
    from node.core.settings import settings

    port = settings.app.MAIN_NODE_PORT
    node = Node(host="127.0.0.1", port=port, is_copy=True)
    await node.initialize()
    if node._mining_task and not node._mining_task.done():
        node._mining_task.cancel()
        try:
            await node._mining_task
        except asyncio.CancelledError:
            pass
    node._mining_task = None
    app.state.blockchain_node = node
    yield
    app.state.blockchain_node = None


def _build_test_app() -> FastAPI:
    from node.routers.api_addons import router as api_addons_router
    from node.routers.blockchain import router as blockchain_router
    from node.routers.gossip import router as gossip_router
    from node.routers.health import router as health_router
    from node.routers.node import router as node_router

    application = FastAPI(lifespan=_test_lifespan)
    application.include_router(health_router, prefix="/health", tags=["health"])
    application.include_router(blockchain_router, prefix="/blockchain", tags=["blockchain"])
    application.include_router(api_addons_router, prefix="/api", tags=["api"])
    application.include_router(node_router, prefix="/nodes", tags=["nodes"])
    application.include_router(gossip_router, prefix="/gossip", tags=["gossip"])
    return application


@pytest_asyncio.fixture
async def app_instance():
    return _build_test_app()


@pytest_asyncio.fixture
async def client(app_instance):
    # httpx ASGITransport does not run Starlette/FastAPI lifespan by default.
    async with app_instance.router.lifespan_context(app_instance):
        transport = ASGITransport(app=app_instance)
        async with AsyncClient(
            transport=transport, base_url="http://test", follow_redirects=True
        ) as ac:
            yield ac


@pytest_asyncio.fixture
async def blockchain_node(client, app_instance):
    """Node from app.state after lifespan startup."""
    return app_instance.state.blockchain_node
