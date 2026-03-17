FROM python:3.12-slim

# Install system dependencies needed by some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock ./

# Install only production dependencies; don't install the project package itself
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

# Copy application source
COPY app/ ./app/

# Copy static data: HCC reference CSV and bundled clinical notes
COPY data/ ./data/

# Create a non-root user and transfer ownership of the app directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser \
    && chown -R appuser:appuser /app

# Output is written here at runtime; declaring as a volume allows the caller
# to bind-mount a host directory so results are persisted outside the container.
VOLUME ["/app/output"]

USER appuser

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Run the FastAPI server
CMD ["poetry", "run", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8080"]
