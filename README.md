# DocuCon API

A simplified document connector and API service built with FastAPI. This service allows authenticated users to upload, retrieve, update, and delete documents, while simulating integration with a document system and vector embedding store. It also includes AI-context preparation through text extraction and chunking.

---

## Features

- ✅ RESTful API with FastAPI
- ✅ JWT-based authentication
- ✅ PostgreSQL-backed user and document metadata storage
- ✅ Mocked document management and vector embedding systems
- ✅ Text extraction and chunking for AI context
- ✅ Alembic-powered migrations
- ✅ Centralized logging and error handling
- ✅ Auto-generated API docs via Swagger UI and ReDoc
- ✅ Unit tests for key services and logic

---

## Project Structure

```bash
DocuCon/
├── app/
│   ├── api/                # API Endpoints (auth, users, documents)
│   ├── core/               # Config, security, logging, exceptions
│   ├── db/                 # Models, engine setup, migrations
│   ├── services/           # Document system, vector store, processors
│   └── schemas/            # Pydantic models for validation
├── tests/                  # Unit and integration tests
├── .env.example            # Sample environment variables
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build instructions
├── docker-compose.yml      # Docker Compose for web and database
└── README.md               # Project documentation
```

---

## Setup Instructions

Follow these steps to run DocuCon locally or via Docker (recommended for consistency).

### Prerequisites

- **Python 3.9+** (for local development)
- **PostgreSQL** (for local development, or use Docker)
- **Docker Desktop** (for containerized setup)

### Environment Variables

Create a `.env` file in the project root based on `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://myuser:mypassword@localhost:5432/document_db
DB_NAME=document_db
DB_USER=myuser
DB_PASSWORD=mypassword
SECRET_KEY=your-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO
TEST_DATABASE_URL=postgresql+asyncpg://myuser:mypassword@localhost:5432/test_document_db
```

For Docker, update `DATABASE_URL` to use the service name `db`:

```env
DATABASE_URL="postgresql+asyncpg://myuser:mypassword@db:5432/document_db"
```

### Clone and Install

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Eyiladeogo/DocuCon
   cd DocuCon
   ```

2. **Local Development (without Docker)**:
   - Create and activate a virtual environment:
     ```bash
     python -m venv venv
     ```
     - Windows: `venv\Scripts\activate`
     - macOS/Linux: `source venv/bin/activate`
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Migrate database:
     ```bash
     alembic upgrade head
     ```
   - Start the App:
     ```bash
     uvicorn app.main:app --reload
     ```

### Docker Setup (Recommended)

1. **Build Docker images**:

   ```bash
   docker compose build
   ```

2. **Start services**:

   ```bash
   docker compose up -d
   ```

   _Note_: Use `docker compose up` to view logs in the terminal.

3. **Run database migrations**:

   ```bash
   docker compose exec web alembic upgrade head
   ```

4. **Stop services**:
   ```bash
   docker compose down -v --remove-orphans
   ```
   _Note_: Omit `-v` to preserve database data for quicker restarts.

**Visit [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.**<br>
**Visit [http://localhost:8000/redoc](http://localhost:8000/redoc) for Redoc UI**

## API Overview

### Auth

- `POST /auth/register` - Register a new user
- `POST /auth/token` - Get JWT token

### Users

- `GET /users/me` - Get current user info

### Documents

- `POST /documents/` - Upload a document
- `GET /documents/` - List documents
- `GET /documents/{id}` - Retrieve a document
- `PUT /documents/{id}` - Update document metadata
- `DELETE /documents/{id}` - Delete a document
- `GET /documents/{id}/chunks` - View document chunks

---

## Architectural Decisions

- **FastAPI**: Chosen for its async support, performance, and auto docs.
- **Modular Structure**: API, core logic, services, and schemas are separated for clarity and scalability.
- **Mocked Services**: The document and vector store are mocked for easy testing.
- **SQLAlchemy + Alembic**: For ORM and migrations.
- **Pydantic**: Ensures strict request validation and response shaping.
- **Custom Exceptions**: All errors funnel through centralized handlers.
- **Dependency Injection**: Used throughout for DB access and authentication logic.

---

## Security Considerations

### Implemented

- ✅ Password hashing (bcrypt)
- ✅ JWT authentication
- ✅ Input validation
- ✅ CORS support (wide-open for dev only)

### Potential Improvements

- Restrict CORS to frontend domains
- Add rate-limiting to sensitive endpoints
- Add refresh tokens and RBAC
- Use a proper secret manager (Vault, AWS Secrets Manager, etc.)
- Enforce HTTPS via proxy in production

---

## Testing

Run tests locally or in Docker for consistent results.

### Local Testing

```bash
# Activate virtual environment
export PYTHONPATH=$(pwd)  # For macOS/Linux
# For Windows (PowerShell): $env:PYTHONPATH = "$(Get-Location)"
python -m pytest tests/
```

### Docker Testing

```bash
docker compose up -d
docker compose exec web python -m pytest tests/
```

**Test Coverage**:

- Token generation and authentication flows
- Document chunking and metadata storage
- Error handling scenarios
