# --- Build stage ---
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies (SQLite)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app -r requirements.txt

# Copy application code
COPY . /app

# --- Runtime stage ---
FROM gcr.io/distroless/python3

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

WORKDIR /app

# Copy installed packages and source code from build stage
COPY --from=builder /app /app

# Expose Flask port
EXPOSE 5000

# Entrypoint
CMD ["app.py"]
