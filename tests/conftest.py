import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy.pool import NullPool  # Import NullPool for better test isolation

from app.main import app
from app.db.database import get_db, Base
from app.db.models import User
from app.core.config import settings
from app.core.security import get_current_user, get_password_hash

# Use the test database URL from settings
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

# Create a test engine with NullPool for better isolation during tests.
# NullPool ensures connections are not reused across greenlets/tasks,
# which can help prevent "another operation in progress" errors.
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

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
    Fixture to set up and tear down the test database for the entire test session.
    Creates all tables before tests and drops them after.
    Ensures the engine is disposed to close connections cleanly.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Explicitly dispose the engine to close all connections at the end of the session.
    # This is crucial for preventing "another operation in progress" errors across test runs.
    await test_engine.dispose()


@pytest.fixture(scope="function")
async def db_session():
    """
    Fixture to provide a clean database session with a transaction for each test function.
    The transaction is rolled back after each test to ensure isolation.
    This prevents test data from leaking between tests.
    """
    async with test_engine.connect() as connection:
        async with connection.begin() as transaction:
            # Bind a session to the connection within the transaction.
            # All operations within this session will be part of this transaction.
            session = TestAsyncSessionLocal(bind=connection)
            try:
                yield session
            finally:
                # Rollback the transaction to clean up changes made by the test.
                # This ensures each test starts with a fresh database state.
                await transaction.rollback()
                # Close the session to release the connection back to the pool (if any)
                # or simply ensure it's not held open.
                await session.close()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Fixture to provide a base AsyncClient for testing FastAPI endpoints.
    It overrides the get_db dependency to use the test session.
    Crucially, it *does not* override get_current_user by default,
    allowing for proper testing of unauthenticated routes.
    """

    # Override the get_db dependency to use the test database session
    app.dependency_overrides[get_db] = lambda: db_session

    # Use AsyncClient with ASGITransport to test the FastAPI app instance
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Clean up overrides after the test to ensure no lingering dependencies.
    # This is vital for test isolation.
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
async def authenticated_client(client: AsyncClient, db_session: AsyncSession):
    """
    Fixture to provide an AsyncClient authenticated as a specific test user.
    This user is created and logged in for each test requiring authentication.
    It builds upon the base 'client' fixture.
    """
    # Create a dedicated user for authentication tests to ensure isolation.
    # We use a unique email to avoid conflicts if multiple authenticated_client
    # fixtures are somehow instantiated in a way that bypasses transaction isolation.
    test_user_email = "docuser@example.com"
    test_user_password = "docpassword"

    # Ensure the user exists in the test database.
    # This part needs to be careful not to conflict with other tests.
    # The db_session fixture's transaction-per-test ensures this is safe.
    user_exists = await db_session.execute(
        select(User).where(User.email == test_user_email)
    )
    test_user = user_exists.scalar_one_or_none()

    if not test_user:
        test_user = User(
            email=test_user_email,
            hashed_password=get_password_hash(test_user_password),
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.commit()  # Commit the user creation within its own transaction
        await db_session.refresh(test_user)

    # Now, override get_current_user for this specific authenticated client's scope
    async def override_get_current_user():
        return test_user

    # Apply the override for the duration of this fixture
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Yield the base client, which now has the authentication override applied
    yield client

    # Clean up the override after the test is done
    app.dependency_overrides.pop(get_current_user, None)
