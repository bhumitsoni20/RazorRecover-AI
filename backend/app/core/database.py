import importlib.util
import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import logger

db_url = settings.DATABASE_URL

# Check if asyncpg is importable; if not and postgresql is configured, fall back to SQLite aiosqlite for local development
try:
    has_asyncpg = importlib.util.find_spec("asyncpg") is not None
except Exception:
    has_asyncpg = False

if db_url.startswith("postgresql://") or db_url.startswith("postgresql+asyncpg://"):
    if has_asyncpg:
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        logger.warning(f"asyncpg module not found. Falling back to local SQLite database ({settings.DATABASE_URL}).")
        db_url = settings.DATABASE_URL
elif db_url.startswith("sqlite://") and not db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

if "sqlite" in db_url and ":///" in db_url:
    prefix, raw_path = db_url.split(":///", 1)
    if not os.path.isabs(raw_path):
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        abs_db_path = os.path.normpath(os.path.join(backend_dir, raw_path)).replace("\\", "/")
        db_url = f"{prefix}:///{abs_db_path}"

engine_kwargs: dict[str, Any] = {"echo": False, "future": True}
if "sqlite" in db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20


engine = create_async_engine(db_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rollback on error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    try:
        async with engine.begin() as conn:
            import app.models  # noqa
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified and initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise
