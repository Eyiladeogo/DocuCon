import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.main import app
from app.db.database import get_db, Base
from app.db.models import User
from app.core.config import settings
from app.core.security import get_current_user, get_password_hash

# Use a separate test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

# Create a test engine and session
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """
    Fixture to set up and tear down the test database.
    Creates all tables before tests and drops them after.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session():
    """
    Fixture to provide a clean database session for each test function.
    Rolls back transactions after each test.
    """
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()  # Rollback changes after each test


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Fixture to provide an AsyncClient for testing FastAPI endpoints.
    Overrides the get_db dependency to use the test session.
    Overrides get_current_user to allow testing protected routes without full auth flow.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # For testing protected routes, we will need a mock user
    async def override_get_current_user():
        # Create a mock user for tests that require authentication
        test_user = User(
            id=1,
            email="testuser@example.com",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
        )
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up overrides after tests
    app.dependency_overrides = {}


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
    # Try to register again with same email
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

    # Attempt to login
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

    # Attempt to login with wrong password
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
    client: AsyncClient, db_session: AsyncSession
):
    """Test /users/me endpoint with an authenticated user."""
    # Register a user
    register_response = await client.post(
        "/auth/register", json={"email": "meuser@example.com", "password": "mepassword"}
    )
    assert register_response.status_code == 201

    # Login to get a token
    login_response = await client.post(
        "/auth/token", data={"username": "meuser@example.com", "password": "mepassword"}
    )
    token = login_response.json()["access_token"]

    # Call /users/me with the token
    response = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "meuser@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_read_users_me_unauthenticated(client: AsyncClient):
    """Test /users/me endpoint without authentication."""
    response = await client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
