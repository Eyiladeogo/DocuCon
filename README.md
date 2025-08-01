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
document_connector/
├── app/
│   ├── api/                # API Endpoints (auth, users, documents)
│   ├── core/               # Config, security, logging, exceptions
│   ├── db/                 # Models, engine setup, migrations
│   ├── services/           # Document system, vector store, processors
│   └── schemas/            # Pydantic models for validation
├── tests/                  # Unit and integration tests
├── .env.example            # Sample environment variables
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- PostgreSQL

### 2. Clone and Install

```bash
git clone https://github.com/Eyiladeogo/DocuCon
cd DocuCon
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file based on `.env.example`:

```env
DATABASE_URL="postgresql+asyncpg://user:password@db_host:db_port/db_name"
SECRET_KEY="your-secret"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL="INFO"
```

### 4. Database Setup

Make sure PostgreSQL is running and the target database exists. Then run:

```bash
alembic upgrade head
```

### 5. Start the App

```bash
uvicorn app.main:app --reload
```

**Visit [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.**<br>
**Visit [http://localhost:8000/redoc](http://localhost:8000/redoc) for Redoc UI**

---

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
- Containerize app with Docker
- Enforce HTTPS via proxy in production

---

## Testing

Run all tests using:

```bash
pytest tests/
```

> **Troubleshooting:**
> If you get errors like `ModuleNotFoundError: No module named 'app'` when running tests, set your project root as the `PYTHONPATH` environment variable. For example:
>
> **In bash or zsh:**
>
> ```bash
> export PYTHONPATH="$(pwd)"
> ```
>
> **In PowerShell:**
>
> ```powershell
> $env:PYTHONPATH = "$(Get-Location)"
> ```

Test coverage includes:

- Token generation and auth flows
- Document chunking and metadata storage
- Error handling scenarios
