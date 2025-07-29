import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import User, Document, DocumentChunk
from app.core.security import get_password_hash
from app.services.mock_doc_system import mock_document_system
from app.services.vector_store import mock_vector_store

# Re-using fixtures from test_auth.py for db_session and client setup
# Ensure test_auth.py (or a conftest.py) defines `setup_test_db`, `db_session`, and `client` fixtures.
# For this example, I'll assume `client` fixture is configured to provide an authenticated user.


@pytest.fixture(scope="function")
async def authenticated_client(client: AsyncClient, db_session: AsyncSession):
    """
    Fixture to provide an AsyncClient authenticated as a specific test user.
    This user is created and logged in for each test requiring authentication.
    """
    # Create a dedicated user for document tests to ensure isolation
    test_user_email = "docuser@example.com"
    test_user_password = "docpassword"

    # Ensure user is registered and active
    user_result = await db_session.execute(
        select(User).where(User.email == test_user_email)
    )
    test_user = user_result.scalar_one_or_none()
    if not test_user:
        test_user = User(
            email=test_user_email,
            hashed_password=get_password_hash(test_user_password),
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.commit()
        await db_session.refresh(test_user)

    # Login and get token
    login_response = await client.post(
        "/auth/token",
        data={"username": test_user_email, "password": test_user_password},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Set Authorization header for the client
    client.headers["Authorization"] = f"Bearer {token}"

    # Override get_current_user to return this specific test_user for all subsequent calls
    # This is important if tests need to assert on the user ID, etc.
    from app.main import app
    from app.core.security import get_current_user

    async def override_get_current_user_for_doc_tests():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user_for_doc_tests

    yield client

    # Clean up client headers and overrides
    del client.headers["Authorization"]
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_document(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test creating a new document."""
    doc_data = {
        "title": "Test Document 1",
        "content": "This is the content of test document 1. It will be chunked.",
    }
    response = await authenticated_client.post("/documents/", json=doc_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == doc_data["title"]
    assert data["content"] == doc_data["content"]
    assert "id" in data
    assert "owner_id" in data
    assert "mock_system_id" in data
    assert data["processed_at"] is not None

    # Verify document in DB
    result = await db_session.execute(select(Document).where(Document.id == data["id"]))
    db_doc = result.scalar_one_or_none()
    assert db_doc is not None
    assert db_doc.title == doc_data["title"]

    # Verify chunks and embeddings were created
    chunk_result = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == data["id"])
    )
    chunks = chunk_result.scalars().all()
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.chunk_text in doc_data["content"]
        assert chunk.embedding_id is not None
        assert await mock_vector_store.get_embedding(chunk.embedding_id) is not None

    # Verify mock system has the document
    assert (
        await mock_document_system.get_document_content(data["mock_system_id"])
        == doc_data["content"]
    )


@pytest.mark.asyncio
async def test_list_documents(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test listing documents for the authenticated user."""
    # Create a few documents
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()

    doc1 = Document(
        title="Doc A",
        content="Content A",
        owner_id=test_user.id,
        mock_system_id="mock1",
    )
    doc2 = Document(
        title="Doc B",
        content="Content B",
        owner_id=test_user.id,
        mock_system_id="mock2",
    )
    db_session.add_all([doc1, doc2])
    await db_session.commit()

    response = await authenticated_client.get("/documents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # May be more if other tests left docs
    titles = [d["title"] for d in data]
    assert "Doc A" in titles
    assert "Doc B" in titles


@pytest.mark.asyncio
async def test_get_document(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test retrieving a single document."""
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()

    doc = Document(
        title="Specific Doc",
        content="Specific Content",
        owner_id=test_user.id,
        mock_system_id="mock_specific",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    response = await authenticated_client.get(f"/documents/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Specific Doc"
    assert data["content"] == "Specific Content"
    assert data["id"] == doc.id


@pytest.mark.asyncio
async def test_get_non_existent_document(authenticated_client: AsyncClient):
    """Test getting a document that does not exist."""
    response = await authenticated_client.get("/documents/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio
async def test_get_document_unauthorized(client: AsyncClient, db_session: AsyncSession):
    """Test getting a document without authentication."""
    # Create a user and a document for them
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()
    doc = Document(
        title="Unauthorized Doc",
        content="Content",
        owner_id=test_user.id,
        mock_system_id="mock_unauth",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    # Try to access without token
    response = await client.get(f"/documents/{doc.id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_update_document_title(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test updating only the title of a document."""
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()
    doc = Document(
        title="Original Title",
        content="Original Content",
        owner_id=test_user.id,
        mock_system_id="mock_update_title",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    update_data = {"title": "New Title"}
    response = await authenticated_client.put(f"/documents/{doc.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["content"] == "Original Content"  # Content should not change

    # Verify in DB
    result = await db_session.execute(select(Document).where(Document.id == doc.id))
    db_doc = result.scalar_one_or_none()
    assert db_doc.title == "New Title"
    assert db_doc.content == "Original Content"


@pytest.mark.asyncio
async def test_update_document_content_reprocesses(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test updating document content triggers reprocessing and new chunks/embeddings."""
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()
    doc = Document(
        title="Reprocess Doc",
        content="Initial short content.",
        owner_id=test_user.id,
        mock_system_id="mock_reprocess",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    # Get initial chunks and embeddings
    initial_chunks_result = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    initial_chunks = initial_chunks_result.scalars().all()
    initial_embedding_ids = [c.embedding_id for c in initial_chunks if c.embedding_id]
    for eid in initial_embedding_ids:
        assert await mock_vector_store.get_embedding(eid) is not None

    new_content = "This is the updated, much longer content for the reprocessed document. It should generate new chunks."
    update_data = {"content": new_content}
    response = await authenticated_client.put(f"/documents/{doc.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == new_content
    assert data["processed_at"] is not None  # Should be updated

    # Verify old embeddings are deleted
    for eid in initial_embedding_ids:
        assert await mock_vector_store.get_embedding(eid) is None

    # Verify new chunks and embeddings in DB
    new_chunks_result = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    )
    new_chunks = new_chunks_result.scalars().all()
    assert len(new_chunks) > 0
    assert len(new_chunks) != len(
        initial_chunks
    )  # Should be different number of chunks
    for chunk in new_chunks:
        assert chunk.chunk_text in new_content
        assert chunk.embedding_id is not None
        assert await mock_vector_store.get_embedding(chunk.embedding_id) is not None


@pytest.mark.asyncio
async def test_delete_document(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test deleting a document."""
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()

    doc_to_delete = Document(
        title="To Delete",
        content="Content to delete.",
        owner_id=test_user.id,
        mock_system_id="mock_to_delete",
    )
    db_session.add(doc_to_delete)
    await db_session.commit()
    await db_session.refresh(doc_to_delete)

    # Add a chunk to ensure its embedding is deleted
    embedding_vector = await mock_vector_store.generate_mock_embedding("chunk content")
    embedding_id = await mock_vector_store.add_embedding(embedding_vector)
    chunk = DocumentChunk(
        document_id=doc_to_delete.id,
        chunk_text="chunk content",
        chunk_order=0,
        embedding_id=embedding_id,
    )
    db_session.add(chunk)
    await db_session.commit()
    await db_session.refresh(chunk)

    # Ensure mock system has it
    await mock_document_system.upload_document(
        doc_to_delete.title, doc_to_delete.content
    )

    response = await authenticated_client.delete(f"/documents/{doc_to_delete.id}")
    assert response.status_code == 204

    # Verify document is deleted from DB
    result = await db_session.execute(
        select(Document).where(Document.id == doc_to_delete.id)
    )
    assert result.scalar_one_or_none() is None

    # Verify chunks are deleted from DB (cascaded)
    chunk_result = await db_session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc_to_delete.id)
    )
    assert len(chunk_result.scalars().all()) == 0

    # Verify embedding is deleted from mock vector store
    assert await mock_vector_store.get_embedding(embedding_id) is None

    # Verify document is deleted from mock document system
    assert (
        await mock_document_system.get_document_content(doc_to_delete.mock_system_id)
        is None
    )


@pytest.mark.asyncio
async def test_delete_non_existent_document(authenticated_client: AsyncClient):
    """Test deleting a document that does not exist."""
    response = await authenticated_client.delete("/documents/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio
async def test_get_document_chunks(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test retrieving chunks for a specific document."""
    user_result = await db_session.execute(
        select(User).where(User.email == "docuser@example.com")
    )
    test_user = user_result.scalar_one_or_none()

    doc_with_chunks = Document(
        title="Chunked Doc",
        content="Chunk 1. Chunk 2. Chunk 3.",
        owner_id=test_user.id,
        mock_system_id="mock_chunks",
    )
    db_session.add(doc_with_chunks)
    await db_session.flush()

    # Manually add chunks to ensure they exist
    chunk_texts = ["Chunk 1.", "Chunk 2.", "Chunk 3."]
    for i, text in enumerate(chunk_texts):
        embedding_vector = await mock_vector_store.generate_mock_embedding(text)
        embedding_id = await mock_vector_store.add_embedding(embedding_vector)
        db_session.add(
            DocumentChunk(
                document_id=doc_with_chunks.id,
                chunk_text=text,
                chunk_order=i,
                embedding_id=embedding_id,
            )
        )
    await db_session.commit()
    await db_session.refresh(doc_with_chunks)

    response = await authenticated_client.get(f"/documents/{doc_with_chunks.id}/chunks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["chunk_text"] == "Chunk 1."
    assert data[1]["chunk_text"] == "Chunk 2."
    assert data[2]["chunk_text"] == "Chunk 3."
    assert data[0]["document_id"] == doc_with_chunks.id
    assert data[0]["embedding_id"] is not None
