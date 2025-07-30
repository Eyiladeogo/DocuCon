from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import (DatabaseOperationException,
                                 DocumentNotFoundException,
                                 DocumentProcessingException,
                                 ForbiddenException)
from app.core.security import get_current_active_user
from app.db.database import get_db
from app.db.models import Document, DocumentChunk, User
from app.schemas.document import (DocumentChunkOut, DocumentCreate,
                                  DocumentOut, DocumentUpdate)
from app.services.document_processor import document_processor
from app.services.mock_doc_system import mock_document_system
from app.services.vector_store import mock_vector_store

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_in: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new document, uploads it to the mock document system,
    processes its content for AI context (chunks), and stores embeddings.
    """
    try:
        # 1. Upload to mock document system
        mock_doc_data = await mock_document_system.upload_document(
            title=doc_in.title, content=doc_in.content
        )
        mock_system_id = mock_doc_data["mock_system_id"]

        # 2. Create document metadata in PostgreSQL
        db_document = Document(
            title=doc_in.title,
            content=doc_in.content,
            owner_id=current_user.id,
            mock_system_id=mock_system_id,
            processed_at=None,  # Will be updated after processing
        )
        db.add(db_document)
        await db.flush()  # Flush to get the document ID before committing

        # 3. Process document for AI context (text extraction and chunking)
        extracted_text = await document_processor.extract_text(doc_in.content)
        chunks = await document_processor.chunk_text(extracted_text)

        # 4. Store chunks and vector embeddings
        for i, chunk_text in enumerate(chunks):
            # Generate mock embedding
            embedding_vector = await mock_vector_store.generate_mock_embedding(
                chunk_text
            )
            embedding_id = await mock_vector_store.add_embedding(embedding_vector)

            db_chunk = DocumentChunk(
                document_id=db_document.id,
                chunk_text=chunk_text,
                chunk_order=i,
                embedding_id=embedding_id,
            )
            db.add(db_chunk)

        # Update document processed_at timestamp
        db_document.processed_at = datetime.now()
        await db.commit()
        await db.refresh(
            db_document
        )  # Refresh to get updated processed_at and relationships

        print(
            f"Document '{doc_in.title}' created and processed for user {current_user.email}"
        )
        return db_document
    except Exception as e:
        await db.rollback()
        print(f"Error creating document: {e}")
        raise DocumentProcessingException(
            detail=f"Failed to create and process document: {e}"
        )


@router.get("/", response_model=List[DocumentOut])
async def list_documents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a list of all documents owned by the current user.
    """
    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    print(f"Listed {len(documents)} documents for user {current_user.email}")
    return documents


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a specific document by its ID.
    Ensures the document belongs to the current user.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise DocumentNotFoundException()
    print(f"Retrieved document ID {document_id} for user {current_user.email}")
    return document


@router.put("/{document_id}", response_model=DocumentOut)
async def update_document(
    document_id: int,
    doc_update: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates an existing document.
    - Only title and content can be updated.
    - Re-processes chunks and embeddings if content changes.
    - Ensures the document belongs to the current user.
    """
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id, Document.owner_id == current_user.id)
    )
    db_document = result.scalar_one_or_none()
    if not db_document:
        raise DocumentNotFoundException()

    original_content = db_document.content
    update_content = False

    if doc_update.title is not None:
        db_document.title = doc_update.title
    if doc_update.content is not None:
        if db_document.content != doc_update.content:
            db_document.content = doc_update.content
            update_content = True

    if update_content:
        try:
            # Delete old chunks and embeddings
            # Iterate over a copy to avoid issues if collection changes during iteration
            chunks_to_delete = list(db_document.chunks)
            for chunk in chunks_to_delete:
                if chunk.embedding_id:
                    await mock_vector_store.delete_embedding(chunk.embedding_id)
                await db.delete(chunk)
            await db.flush()  # Ensure deletions are processed before adding new ones

            # Re-process document for AI context
            extracted_text = await document_processor.extract_text(db_document.content)
            chunks = await document_processor.chunk_text(extracted_text)

            # Store new chunks and vector embeddings
            for i, chunk_text in enumerate(chunks):
                embedding_vector = await mock_vector_store.generate_mock_embedding(
                    chunk_text
                )
                embedding_id = await mock_vector_store.add_embedding(embedding_vector)

                db_chunk = DocumentChunk(
                    document_id=db_document.id,
                    chunk_text=chunk_text,
                    chunk_order=i,
                    embedding_id=embedding_id,
                )
                db.add(db_chunk)

            db_document.processed_at = datetime.now()
            print(f"Document ID {document_id} content updated and re-processed.")
        except Exception as e:
            await db.rollback()  # Rollback changes if processing fails
            print(f"Error re-processing document {document_id}: {e}")
            raise DocumentProcessingException(
                detail=f"Failed to re-process document content: {e}"
            )

    await db.commit()
    await db.refresh(db_document)
    print(f"Document ID {document_id} updated for user {current_user.email}")
    return db_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a document by its ID.
    - Also deletes associated chunks and embeddings.
    - Ensures the document belongs to the current user.
    """
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id, Document.owner_id == current_user.id)
    )
    db_document = result.scalar_one_or_none()
    if not db_document:
        raise DocumentNotFoundException()

    try:
        # Delete from mock document system
        await mock_document_system.delete_document(db_document.mock_system_id)

        # Chunks are set to cascade delete with the document, but explicitly deleting embeddings
        for chunk in db_document.chunks:
            if chunk.embedding_id:
                await mock_vector_store.delete_embedding(chunk.embedding_id)

        # Delete document from PostgreSQL (chunks will cascade delete)
        await db.delete(db_document)
        await db.commit()
        print(
            f"Document ID {document_id} and its chunks/embeddings deleted for user {current_user.email}"
        )
    except Exception as e:
        await db.rollback()
        print(f"Error deleting document {document_id}: {e}")
        raise DatabaseOperationException(detail=f"Failed to delete document: {e}")


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkOut])
async def get_document_chunks(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves all chunks for a specific document.
    Ensures the document belongs to the current user.
    """
    # First, verify document ownership
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.owner_id == current_user.id
        )
    )
    document = doc_result.scalar_one_or_none()
    if not document:
        raise DocumentNotFoundException()

    # Then, retrieve chunks
    chunk_result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_order)
    )
    chunks = chunk_result.scalars().all()
    print(f"Retrieved {len(chunks)} chunks for document ID {document_id}")
    return chunks
