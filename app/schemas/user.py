from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr = Field(..., example="user@example.com")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, example="securepassword123")


class UserLogin(UserBase):
    """Schema for user login."""

    password: str = Field(..., example="securepassword123")


class UserOut(UserBase):
    """Schema for returning user data (excludes sensitive info like password)."""

    id: int
    is_active: bool = True

    class Config:
        from_attributes = True  # Allows Pydantic to read data from ORM models
