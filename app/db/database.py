from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.exceptions import DatabaseOperationException

# Create an asynchronous engine
# connect_args={"check_same_thread": False} is for SQLite, not strictly needed for PostgreSQL
# but often seen in examples. For asyncpg, it's not relevant.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production for less verbose logging
    pool_size=10,  # Adjust based on expected load
    max_overflow=20,  # Adjust based on expected load
)

# Create an asynchronous session local
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Important for keeping objects in session after commit
)

Base = declarative_base()


async def get_db():
    """
    Dependency that provides an asynchronous database session.
    It ensures the session is closed after the request is processed.
    """
    db = AsyncSessionLocal()
    try:
        yield db
    except Exception as e:
        await db.rollback()  # Rollback on any exception
        raise DatabaseOperationException(detail=f"Database error: {e}")
    finally:
        await db.close()
