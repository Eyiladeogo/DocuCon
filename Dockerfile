FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2 (asyncpg)
# This is crucial for connecting to PostgreSQL from within the container
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    # Clean up APT cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the working directory and install
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

EXPOSE 8000

# ENV DATABASE_URL="postgresql+asyncpg://user:password@db:5432/document_db"
ENV SECRET_KEY="docker-secret-key"
ENV ALGORITHM="HS256"
ENV ACCESS_TOKEN_EXPIRE_MINUTES=30
ENV LOG_LEVEL="INFO"

# Command to run the application using Uvicorn
# --host 0.0.0.0 makes the app accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
