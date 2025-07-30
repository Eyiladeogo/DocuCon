from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    """
    SQLAlchemy ORM model for users.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    documents = relationship("Document", back_populates="owner")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Document(Base):
    """
    SQLAlchemy ORM model for document metadata.
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    # Storing content directly in DB for simplicity, but in a real app,
    # this might be a path/reference to a file storage system.
    content = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mock_system_id = Column(
        String, unique=True, index=True, nullable=False
    )  # ID from the mock external system
    processed_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When document was processed for AI context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    owner = relationship("User", back_populates="documents")
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Document(id={self.id}, title='{self.title}', owner_id={self.owner_id})>"
        )


class DocumentChunk(Base):
    """
    SQLAlchemy ORM model for document chunks and their associated embedding IDs.
    """

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_order = Column(
        Integer, nullable=False
    )  # Order of the chunk within the document
    embedding_id = Column(
        String, unique=True, index=True, nullable=True
    )  # ID from the mock vector store

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_order", name="_document_chunk_order_uc"),
    )

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, order={self.chunk_order})>"
