FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Using pip and a requirements.txt if present, otherwise install common deps
COPY requirements.txt .
RUN pip install --upgrade pip
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; else pip install fastapi uvicorn sqlalchemy alembic; fi

# Copy application code
COPY . .

# Expose port (FastAPI default 8000)
EXPOSE 8000

# Command to run the app (assuming FastAPI with uvicorn)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]