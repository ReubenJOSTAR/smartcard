"""Async SQLAlchemy engine + session factory — placeholder.
See progress.md → Backend — Core → "Async SQLAlchemy engine + session factory".
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

engine: AsyncEngine
async_session_factory: async_sessionmaker[AsyncSession]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    ...
