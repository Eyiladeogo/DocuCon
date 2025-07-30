import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import User


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, db_session: AsyncSession):
    """Test successful user registration."""
    response = await client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert data["is_active"] is True

    # Verify user is in DB
    result = await db_session.execute(
        select(User).where(User.email == "newuser@example.com")
    )
    user_in_db = result.scalar_one_or_none()
    assert user_in_db is not None
    assert user_in_db.email == "newuser@example.com"


@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient):
    """Test registration with an already existing email."""
    # Register first user
    await client.post(
        "/auth/register",
        json={"email": "existing@example.com", "password": "password123"},
    )
    # Try to register again with the same email
    response = await client.post(
        "/auth/register",
        json={"email": "existing@example.com", "password": "anotherpassword"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_for_access_token(client: AsyncClient):
    """Test successful user login and token generation."""
    # Register a user first
    await client.post(
        "/auth/register",
        json={"email": "loginuser@example.com", "password": "loginpassword"},
    )

    # Now try to log in
    response = await client.post(
        "/auth/token",
        data={"username": "loginuser@example.com", "password": "loginpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with incorrect password."""
    # Register a user
    await client.post(
        "/auth/register",
        json={"email": "wrongpass@example.com", "password": "correctpassword"},
    )

    # Try to login with wrong password
    response = await client.post(
        "/auth/token",
        data={"username": "wrongpass@example.com", "password": "incorrectpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_login_non_existent_user(client: AsyncClient):
    """Test login with a non-existent user."""
    response = await client.post(
        "/auth/token",
        data={"username": "nonexistent@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_read_users_me_authenticated(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """Test /users/me endpoint with an authenticated user."""
    # The authenticated_client fixture already ensures a user is created
    # and the client is set up to act as that user.
    # The mock user email is 'docuser@example.com' from conftest.py

    # Call /users/me with the authenticated client
    response = await authenticated_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "docuser@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_read_users_me_unauthenticated(client: AsyncClient):
    """Test /users/me endpoint without authentication."""
    # This test uses the base 'client' fixture, which does NOT override get_current_user.
    # Therefore, it should correctly return 401 Unauthorized.
    response = await client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
