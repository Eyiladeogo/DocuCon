import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import auth, documents, users
from app.core.config import settings
from app.core.exceptions import DocumentConnectorException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DocuCon API",
    description="A simplified RESTful API for document management, processing, and AI context.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)


# Global exception handler for custom DocumentConnectorException
@app.exception_handler(DocumentConnectorException)
async def document_connector_exception_handler(
    request: Request, exc: DocumentConnectorException
):
    logger.error(
        f"DocumentConnectorException caught: {exc.detail} (Status: {exc.status_code})"
    )
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers
    )


@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return {"message": "Welcome to the DocuCon API. Visit /docs for API documentation."}


@app.router.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")

    from app.db.database import engine

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful.")


@app.router.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    # Close database connections if not handled by session manager
    from app.db.database import engine

    await engine.dispose()
