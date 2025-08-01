import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class DocumentConnectorException(HTTPException):
    """Base exception for the Document Connector application."""

    def __init__(self, status_code: int, detail: str, headers: dict = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class UserNotFoundException(DocumentConnectorException):
    """Exception raised when a user is not found."""

    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class InvalidCredentialsException(DocumentConnectorException):
    """Exception raised for invalid authentication credentials."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class DocumentNotFoundException(DocumentConnectorException):
    """Exception raised when a document is not found."""

    def __init__(self, detail: str = "Document not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DocumentProcessingException(DocumentConnectorException):
    """Exception raised for errors during document processing (e.g., text extraction, chunking)."""

    def __init__(self, detail: str = "Document processing failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class DatabaseOperationException(DocumentConnectorException):
    """Exception raised for errors during database operations."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class ForbiddenException(DocumentConnectorException):
    """Exception raised when a user does not have permission to perform an action."""

    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def http_exception_handler(request: Request, exc: DocumentConnectorException):
    """
    Handles custom DocumentConnectorException and its subclasses,
    returning a standardized JSON response.
    """
    logger.error(
        f"DocumentConnectorException caught: {exc.detail} (Status: {exc.status_code}) "
        f"for URL: {request.url}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )
