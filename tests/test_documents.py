import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Document, DocumentChunk, User


@pytest.mark.asyncio
async def test_create_document(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test successful document creation."""
    response = await authenticated_client.post(
        "/documents/",
        json={"title": "My Test Document", "content": "This is the content."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Test Document"
    assert data["content"] == "This is the content."
    assert "id" in data
    assert "owner_id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Verify document is in DB
    result = await db_session.execute(
        select(Document).where(Document.title == "My Test Document")
    )
    doc_in_db = result.scalar_one_or_none()
    assert doc_in_db is not None
    assert doc_in_db.title == "My Test Document"


@pytest.mark.asyncio
async def test_list_documents(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test listing documents for the authenticated user."""
    # Create a few documents for the authenticated user
    await authenticated_client.post(
        "/documents/", json={"title": "Doc 1", "content": "Content 1"}
    )
    await authenticated_client.post(
        "/documents/", json={"title": "Doc 2", "content": "Content 2"}
    )

    response = await authenticated_client.get("/documents/")
    assert response.status_code == 200
    data = response.json()
    assert (
        len(data) >= 2
    )  # Should be at least 2, plus any created by other tests if not perfectly isolated
    assert any(d["title"] == "Doc 1" for d in data)
    assert any(d["title"] == "Doc 2" for d in data)


@pytest.mark.asyncio
async def test_get_document(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test retrieving a single document by ID."""
    create_response = await authenticated_client.post(
        "/documents/", json={"title": "Single Doc", "content": "Single Content"}
    )
    doc_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["title"] == "Single Doc"
    assert data["content"] == "Single Content"


@pytest.mark.asyncio
async def test_get_non_existent_document(authenticated_client: AsyncClient):
    """Test retrieving a non-existent document."""
    response = await authenticated_client.get(
        "/documents/99999"
    )  # Assuming 99999 does not exist
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio
async def test_get_document_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """Test getting a document without authentication."""
    # Create a user and a document for them using a direct db_session operation
    # to ensure it's in the DB for this test, without relying on client auth.
    test_user = User(
        email="unauth_doc_owner@example.com",
        hashed_password="hashedpassword",
        is_active=True,
    )
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    doc = Document(
        title="Unauthorized Doc",
        content="This document requires auth.",
        owner_id=test_user.id,
        mock_system_id="mock_unauth_doc_id",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    # Use the base client (unauthenticated) to try and access the document
    response = await client.get(f"/documents/{doc.id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_document_title(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test updating a document's title."""
    create_response = await authenticated_client.post(
        "/documents/", json={"title": "Old Title", "content": "Some content"}
    )
    doc_id = create_response.json()["id"]

    update_response = await authenticated_client.put(
        f"/documents/{doc_id}", json={"title": "New Title", "content": "Some content"}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == doc_id
    assert data["title"] == "New Title"
    assert data["content"] == "Some content"

    # Verify in DB
    result = await db_session.execute(select(Document).where(Document.id == doc_id))
    doc_in_db = result.scalar_one_or_none()
    assert doc_in_db.title == "New Title"


@pytest.mark.asyncio
async def test_update_document_content_reprocesses(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test updating document content triggers reprocessing (mocked)."""
    # First, create a document with initial content
    initial_content = "Original content for chunking."
    create_response = await authenticated_client.post(
        "/documents/", json={"title": "Reprocess Doc", "content": initial_content}
    )
    doc_id = create_response.json()["id"]

    # Assert initial chunks (mocked)
    initial_chunks_response = await authenticated_client.get(
        f"/documents/{doc_id}/chunks"
    )
    assert initial_chunks_response.status_code == 200
    assert len(initial_chunks_response.json()) > 0
    assert initial_chunks_response.json()[0]["chunk_text"] == initial_content

    # Update the document content
    updated_content = "Updated content for new chunks."
    update_response = await authenticated_client.put(
        f"/documents/{doc_id}",
        json={"title": "Reprocess Doc", "content": updated_content},
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["content"] == updated_content

    # Assert new chunks (mocked)
    updated_chunks_response = await authenticated_client.get(
        f"/documents/{doc_id}/chunks"
    )
    assert updated_chunks_response.status_code == 200
    assert len(updated_chunks_response.json()) > 0
    assert updated_chunks_response.json()[0]["chunk_text"] == updated_content


@pytest.mark.asyncio
async def test_delete_document(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test deleting a document."""
    create_response = await authenticated_client.post(
        "/documents/", json={"title": "Doc to Delete", "content": "Content to delete"}
    )
    doc_id = create_response.json()["id"]

    response = await authenticated_client.delete(f"/documents/{doc_id}")
    assert response.status_code == 204

    # Verify document is deleted from DB
    result = await db_session.execute(select(Document).where(Document.id == doc_id))
    doc_in_db = result.scalar_one_or_none()
    assert doc_in_db is None


@pytest.mark.asyncio
async def test_delete_non_existent_document(authenticated_client: AsyncClient):
    """Test deleting a non-existent document."""
    response = await authenticated_client.delete("/documents/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio
async def test_get_document_chunks(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test retrieving chunks for a specific document."""
    # The authenticated_client fixture already ensures a user is created.
    # We'll use this user's ID for the document.
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()
    assert test_user is not None  # Ensure the mock user exists

    doc_with_chunks = Document(
        title="Chunked Doc",
        content="Chunk 1. Chunk 2. Chunk 3.",
        owner_id=test_user.id,
        mock_system_id="mock_chunks",
    )
    db_session.add(doc_with_chunks)
    await db_session.flush()  # Flush to get the document ID before adding chunks

    # Manually add chunks to ensure they exist for this test.
    chunk_texts = ["Chunk 1.", "Chunk 2.", "Chunk 3."]
    for i, text in enumerate(chunk_texts):
        db_session.add(
            DocumentChunk(
                document_id=doc_with_chunks.id,
                chunk_text=text,
                chunk_order=i,
                embedding_id=f"mock_embedding_{i}",  # Mock an embedding ID
            )
        )
    await db_session.commit()  # Commit chunks
    await db_session.refresh(doc_with_chunks)  # Refresh to load relationships if needed

    response = await authenticated_client.get(f"/documents/{doc_with_chunks.id}/chunks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["chunk_text"] == "Chunk 1."
    assert data[1]["chunk_text"] == "Chunk 2."
    assert data[2]["chunk_text"] == "Chunk 3."
    assert data[0]["document_id"] == doc_with_chunks.id
