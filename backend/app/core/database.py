from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logging import logger

db_url = settings.DATABASE_URL

# Check if asyncpg is importable; if not and postgresql is configured, fall back to SQLite aiosqlite for local development
has_asyncpg = False
try:
    import asyncpg  # noqa
    has_asyncpg = True
except ImportError:
    has_asyncpg = False

if db_url.startswith("postgresql://") or db_url.startswith("postgresql+asyncpg://"):
    if has_asyncpg:
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        logger.warning("asyncpg module not found. Falling back to local SQLite database (sqlite+aiosqlite:///./razorrecover.db).")
        db_url = "sqlite+aiosqlite:///./razorrecover.db"
elif db_url.startswith("sqlite://") and not db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

engine_kwargs = {"echo": False, "future": True}
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

Base = declarative_base()


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
