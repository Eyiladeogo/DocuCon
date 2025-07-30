from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings
from app.core.exceptions import DatabaseOperationException

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production for less verbose logging
    pool_size=10,
    max_overflow=20,
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
