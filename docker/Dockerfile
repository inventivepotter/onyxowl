# Multi-stage Dockerfile for Privacy Filter API
# Builder pattern for optimized image size

# ============================================================================
# Stage 1: Builder - Install dependencies and download models
# ============================================================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv

# Activate virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (optional, GLiNER is primary)
RUN python -m spacy download en_core_web_sm || echo "spaCy model download skipped"

# Pre-download GLiNER model to cache it
COPY download_models.py .
RUN python download_models.py || echo "GLiNER model will download on first use"

# ============================================================================
# Stage 2: Runtime - Lightweight production image
# ============================================================================
FROM python:3.11-slim AS runtime

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="Privacy Filter API with GLiNER + Presidio"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy GLiNER model cache from builder (if downloaded)
COPY --from=builder /root/.cache /root/.cache

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # GLiNER settings
    TRANSFORMERS_CACHE=/root/.cache/huggingface \
    HF_HOME=/root/.cache/huggingface \
    # Uvicorn settings
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1 \
    LOG_LEVEL=info

# Copy application code
COPY privacy_filter.py .
COPY api_endpoint.py .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /root/.cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "api_endpoint:app", "--host", "0.0.0.0", "--port", "8000"]
