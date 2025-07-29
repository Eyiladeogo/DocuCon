from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DocumentBase(BaseModel):
    """Base schema for document data."""

    title: str = Field(
        ..., min_length=1, max_length=255, example="My Important Research Paper"
    )
    content: str = Field(
        ...,
        example="This is the full content of my research paper, detailing various findings...",
    )


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""

    # No additional fields needed for creation beyond base
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, example="Updated Research Paper Title"
    )
    content: Optional[str] = Field(
        None, example="Updated content for the research paper."
    )


class DocumentOut(DocumentBase):
    """Schema for returning document data."""

    id: int
    owner_id: int
    mock_system_id: str = Field(..., example="mock_doc_12345")
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read data from ORM models


class DocumentChunkOut(BaseModel):
    """Schema for returning document chunk data."""

    id: int
    document_id: int
    chunk_text: str
    chunk_order: int
    embedding_id: Optional[str] = Field(
        None, example="vec_embed_abcde"
    )  # ID from the mock vector store

    class Config:
        from_attributes = True
