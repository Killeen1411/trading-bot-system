"""
Shared async engine + session dependency for all dashboard routers.
Extracted out of main.py now that there's more than one file that needs it.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from dashboard import config


def _normalize(url: str) -> str:
    # Render (and some other providers) hand out postgres:// — SQLAlchemy's
    # async driver needs the postgresql+asyncpg:// form.
    url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(_normalize(config.DATABASE_URL), echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
