"""Shared pytest fixtures. See api/CLAUDE.md → Test Structure."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import async_session_factory, engine
from app.core.redis import redis_pool
from app.main import app


@pytest.fixture(autouse=True)
async def _reset_shared_connections():
    # The Redis client and SQLAlchemy engine are module-level singletons whose
    # pooled connections bind to whichever event loop first uses them. Each test
    # gets its own fresh event loop (pytest-asyncio's function-scoped default), so
    # a connection left open from the previous test's loop breaks on next use
    # (Windows Proactor raises "attached to a different loop"). Disposing both
    # pools after every test forces a fresh connection, bound to the *next*
    # test's loop, on next use.
    await redis_pool.flushdb()
    yield
    await redis_pool.aclose()
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def test_user():
    ...


@pytest.fixture
async def test_store():
    ...


@pytest.fixture
async def test_product():
    ...


@pytest.fixture
async def active_session():
    ...
