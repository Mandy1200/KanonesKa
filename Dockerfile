FROM python:3.11-slim

# Install minimal build dependencies for packages like FAISS or sentence-transformers
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application directories
COPY src/ ./src/
COPY api/ ./api/
COPY data/ ./data/
COPY frontend_react/dist/ ./frontend_react/dist/
COPY .env .env

EXPOSE 8000

# Command to run uvicorn server serving both api and static frontend
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
