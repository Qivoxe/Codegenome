from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./codegenome.db")

# Render/Heroku-style URLs come as postgres:// or postgresql://
# SQLAlchemy's async engine needs the +asyncpg driver in the scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


def init_db() -> None:
    from sqlalchemy import create_engine
    # Strip async driver for the sync engine used here
    sync_url = DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
    sync_engine = create_engine(sync_url)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()


async def close_db() -> None:
    await engine.dispose()
