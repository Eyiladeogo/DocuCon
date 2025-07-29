from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Schema for the JWT access token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for the data contained within the JWT token payload."""

    email: Optional[str] = None
    id: Optional[int] = None  # User ID
