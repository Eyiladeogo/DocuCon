import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.api import auth, documents, users
from app.core.config import settings
from app.core.exceptions import (DocumentConnectorException,
                                 http_exception_handler)
from app.db.database import engine, get_db
from app.db.models import Base

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    MAX_RETRIES = 10
    RETRY_DELAY = 3
    for i in range(MAX_RETRIES):
        try:
            logger.info(
                f"Attempting to connect to database (retry {i+1}/{MAX_RETRIES})..."
            )
            async with engine.connect() as conn:
                await conn.run_sync(Base.metadata.reflect)
            logger.info("Database connection successful!")
            break
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            if i < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.critical(
                    "Max database connection retries reached. Exiting application."
                )
                raise
        except Exception as e:
            logger.critical(
                f"An unexpected error occurred during database connection: {e}"
            )
            raise

    yield

    logger.info("Application shutting down...")
    await engine.dispose()
    logger.info("Database connection pool disposed.")


app = FastAPI(
    title="Document Connector API",
    description="API for document management, processing, and AI context.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)

app.add_exception_handler(DocumentConnectorException, http_exception_handler)
