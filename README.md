# Document Connector API

A simplified RESTful API for document management, processing for AI context, and metadata storage. This project demonstrates a basic backend service built with FastAPI, SQLAlchemy (with AsyncPG), and a mock external document system and vector store.

## Features

- **RESTful API:** Standard CRUD operations for documents.
- **User Authentication:** JWT-based authentication for secure access.
- **Mock Document System:** Simulates an external document management API for document content storage.
- **Document Processing:** Mock text extraction and chunking for AI context.
- **PostgreSQL Metadata Storage:** Stores document and user metadata using SQLAlchemy ORM.
- **Mock Vector Embeddings:** In-memory storage for simulated vector embeddings of document chunks.
- **Comprehensive Error Handling:** Custom exceptions and global exception handling.
- **Logging:** Basic logging for application events.
- **Automatic API Documentation:** Provided by FastAPI (Swagger UI and ReDoc).

## Project Structure

document_connector/
├── app/
│ ├── api/ # API Endpoints (auth, users, documents)
│ ├── core/ # Core utilities (config, security, exceptions)
│ ├── db/ # Database setup (engine, models, migrations)
│ ├── services/ # Business logic & external integrations (mock doc system, processor, vector store)
│ └── schemas/ # Pydantic models for data validation and serialization
├── tests/ # Unit and integration tests
├── .env.example # Example environment variables
├── requirements.txt # Python dependencies
└── README.md # Project documentation (this file)

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- PostgreSQL database (local or remote)

### 2. Clone the Repository

````bash
git clone <repository_url> # Replace with your repository URL
cd document_connector


3. Create a Virtual Environment and Install Dependencies

```bash
python -m venv venv
# On Unix/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
pip install -r requirements.txt
````

4. Environment Variables

Create a `.env` file in the root directory of the project based on `.env.example`.

```env
# .env
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/document_db"
SECRET_KEY="your-very-secret-key-here-change-this-in-production"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL="INFO"
```

**Important:**

- Replace `user`, `password`, `localhost:5432`, and `document_db` with your PostgreSQL credentials and database details.
- Change `SECRET_KEY` to a strong, randomly generated string for production.

5. Database Setup and Migrations

First, ensure your PostgreSQL database (`document_db` or whatever you named it) exists and the user has permissions.

While Alembic is configured, for a quick start, you can manually apply the initial schema.

**Using Alembic (Recommended for production):**

**Initialize Alembic** (if not already done, usually once per project):

```bash
alembic init -t async app/db/migrations
```

This creates `alembic.ini` and the `app/db/migrations` directory structure.

**Edit `alembic.ini`:**

- Set `sqlalchemy.url` under `[alembic]` to your `DATABASE_URL` from `.env`.
- Ensure `script_location` points to `app/db/migrations`.

**Edit `app/db/migrations/env.py`:**

Import your Base from `app.db.database`:

```python
from app.db.database import Base
target_metadata = Base.metadata
```

Modify `run_migrations_online` to use asyncpg engine:

```python
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(settings.DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()
```

**Generate the initial migration** (this will compare your models to an empty database):

```bash
alembic revision --autogenerate -m "Initial schema"
```

**Apply the migration:**

```bash
alembic upgrade head
```

**Manual SQL (For quick testing/understanding):**

You can also directly execute the SQL commands from `app/db/migrations/versions/initial_schema.sql` in your PostgreSQL client (e.g., psql).

6. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables live-reloading during development.
The API will be accessible at [http://localhost:8000](http://localhost:8000).

7. Access API Documentation

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## API Endpoints

### Authentication (`/auth`):

- `POST /auth/register`: Register a new user.
- `POST /auth/token`: Get JWT token for authentication.

### Users (`/users`):

- `GET /users/me`: Get details of the current authenticated user. (Requires JWT)

### Documents (`/documents`):

- `POST /documents/`: Create a new document. (Requires JWT)
- `GET /documents/`: List user's documents. (Requires JWT)
- `GET /documents/{document_id}`: Get a specific document. (Requires JWT)
- `PUT /documents/{document_id}`: Update a document. (Requires JWT)
- `DELETE /documents/{document_id}`: Delete a document. (Requires JWT)
- `GET /documents/{document_id}/chunks`: Get chunks for a document. (Requires JWT)

Architectural Decisions
FastAPI for API Service: Chosen for its high performance (built on Starlette and Pydantic), asynchronous capabilities, and automatic API documentation generation, which aligns perfectly with the requirements.

Modular Project Structure: The application is organized into logical directories (api, core, db, services, schemas, tests) to promote separation of concerns, maintainability, and scalability. Each module has a clear responsibility.

SQLAlchemy ORM with AsyncPG: Selected for robust database interactions with PostgreSQL. AsyncPG ensures non-blocking I/O for database operations, complementing FastAPI's asynchronous nature. SQLAlchemy's ORM provides an object-oriented way to interact with the database, abstracting SQL queries.

Pydantic for Data Validation: Used extensively for request body validation, response serialization, and environment variable management (pydantic-settings). This ensures data integrity and provides clear API contracts.

JWT Authentication: A standard and secure method for stateless authentication, suitable for RESTful APIs. python-jose and passlib[bcrypt] are used for token handling and password hashing, respectively.

Dependency Injection: FastAPI's dependency injection system (Depends) is heavily utilized for managing database sessions, current user authentication, and other service dependencies. This makes the code testable and organized.

Mock Services: MockDocumentSystem and MockVectorStore are implemented as in-memory simulations. This allows the core API logic to be developed and tested independently without requiring actual external services, fulfilling the "mock" requirement. In a real-world scenario, these would be replaced with integrations to actual document management systems (e.g., AWS S3, Google Drive API) and vector databases (e.g., Pinecone, Weaviate, Milvus, pgvector).

Centralized Error Handling: Custom exceptions (DocumentConnectorException and its subclasses) are defined and handled globally in app/main.py. This provides consistent error responses across the API and simplifies error management in individual endpoints.

Alembic for Database Migrations: While manually applied for initial setup in this README, Alembic is included in requirements.txt and is the standard tool for managing database schema changes in a version-controlled manner, crucial for production environments.

Security Considerations and Potential Improvements
Current Security Measures
Password Hashing: Passwords are never stored in plain text; bcrypt is used for strong hashing.

JWT Authentication: Access tokens are used for authentication, providing a stateless mechanism.

HTTPS (Implied): While not configured directly in uvicorn, FastAPI applications should always be deployed behind a reverse proxy (like Nginx or Caddy) that enforces HTTPS to encrypt all traffic.

Input Validation: Pydantic schemas provide robust input validation, preventing common injection attacks (e.g., SQL injection through malformed JSON, though SQLAlchemy also helps prevent direct SQL injection).

CORS Configuration: Configured to allow all origins for development ease.

Potential Improvements
Strict CORS Policy: In production, allow_origins=["*"] should be replaced with a list of specific trusted frontend domains (e.g., https://yourfrontend.com).

Rate Limiting: Implement rate limiting on authentication endpoints (/auth/register, /auth/token) to prevent brute-force attacks. Libraries like fastapi-limiter can be used.

Role-Based Access Control (RBAC): Extend the user model to include roles (e.g., admin, editor, viewer) and implement permissions checks in API endpoints to restrict access to certain operations based on the user's role.

Token Refresh Mechanism: For long-lived sessions, implement refresh tokens to minimize the exposure time of access tokens.

Secure Secret Management: Instead of .env files, use a dedicated secret management system (e.g., AWS Secrets Manager, Google Secret Manager, HashiCorp Vault) for SECRET_KEY and database credentials in production.

Detailed Logging: Enhance logging to include request IDs, user IDs, and more context for better traceability and debugging, especially for security audits. Consider structured logging (e.g., JSON logs).

Containerization (Docker): Provide a Dockerfile and docker-compose.yml for easier deployment and environment consistency.

Health Checks: Add a /health or /status endpoint for monitoring the application's health.

Asynchronous Background Tasks: For long-running document processing (e.g., actual text extraction from large files, complex embedding generation), offload these tasks to a background worker system (e.g., Celery with Redis/RabbitMQ) to keep API responses fast.

Actual Document Storage & Vector DB: Replace mock services with integrations to real cloud storage (e.g., S3, GCS) and a dedicated vector database (e.g., Pinecone, Weaviate, Qdrant, pgvector).

Comprehensive Unit/Integration Tests: Expand test coverage significantly, including edge cases, error conditions, and performance benchmarks.

Testing Approach
Unit tests for key components (e.g., security functions, document processing logic) are included in the tests/ directory. Integration tests for API endpoints will simulate HTTP requests to verify end-to-end functionality.

To run tests:

pytest tests/

```

```
