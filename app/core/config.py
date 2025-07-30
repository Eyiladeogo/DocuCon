import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/document_db"
    TEST_DATABASE_URL: str = (
        "postgresql+asyncpg://user:password@localhost:5432/test_document_db"
    )

    # JWT settings
    SECRET_KEY: str = "super-secret-key-replace-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # Mock document system settings (if needed, though not strictly used in config)
    # MOCK_DOC_SYSTEM_BASE_URL: str = "http://mock-doc-system:8001"


settings = Settings()
