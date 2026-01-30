from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.config import settings

# For Neon/Postgres, we use the DATABASE_URL from settings
DATABASE_URL = settings.DATABASE_URL

# Ensure the driver is asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# asyncpg does not support 'sslmode' or 'channel_binding' as separate arguments in some versions
# when passed via SQLAlchemy. We strip them from the URL query string.
if "?" in DATABASE_URL:
    base_url, query_params = DATABASE_URL.split("?", 1)
    # Strip problematic parameters for asyncpg
    problematic = ["sslmode=", "channel_binding="]
    params = [p for p in query_params.split("&") if not any(p.startswith(bad) for bad in problematic)]
    DATABASE_URL = base_url + ("?" + "&".join(params) if params else "")

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"ssl": True} if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
