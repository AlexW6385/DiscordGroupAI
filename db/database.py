from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

# Create the async engine
# Note: Ensure the URL uses asyncpg for PostgreSQL async support
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create a customized AsyncSession class
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()

# Dependency to get a database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
