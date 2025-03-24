FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Accept build arguments for flexible caching
ARG BUILDKIT_INLINE_CACHE=1
ARG PIP_CACHE_DIR=/pip-cache

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel setuptools

# Copy requirements first to maximize cache hits
COPY requirements.txt .

# Split requirements into smaller groups for better layer caching and parallel installation
RUN grep -v "langchain\|transformers\|torch\|huggingface\|sentence-transformers\|pydantic\|numpy\|pandas\|scikit-learn" requirements.txt > small_requirements.txt && \
    grep "pydantic\|numpy\|pandas\|scikit-learn" requirements.txt > basic_ai_requirements.txt && \
    grep "langchain" requirements.txt > langchain_requirements.txt && \
    grep "transformers\|torch\|huggingface\|sentence-transformers" requirements.txt > heavy_ai_requirements.txt

# Create wheel directories with volume mount points for caching
RUN mkdir -p /wheels/small /wheels/basic /wheels/langchain /wheels/heavy

# Build wheels in parallel with optimized cache settings
RUN pip wheel --wheel-dir=/wheels/small -r small_requirements.txt

# Build wheels for basic AI libraries
RUN pip wheel --wheel-dir=/wheels/basic --find-links=/wheels/small -r basic_ai_requirements.txt

# Build wheels for langchain libraries
RUN pip wheel --wheel-dir=/wheels/langchain --find-links=/wheels/small --find-links=/wheels/basic -r langchain_requirements.txt

# Build wheels for heavy AI libraries with parallel downloads
RUN pip wheel --wheel-dir=/wheels/heavy --find-links=/wheels/small --find-links=/wheels/basic --find-links=/wheels/langchain -r heavy_ai_requirements.txt

# Final production stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/service

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    libmagic1 \
    postgresql-server-dev-all \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install in batches for efficient layer caching
COPY --from=builder /wheels/small /wheels/small
COPY --from=builder /wheels/basic /wheels/basic 
COPY --from=builder /wheels/langchain /wheels/langchain
COPY --from=builder /wheels/heavy /wheels/heavy

# Install all wheels in one command to reduce image layers
RUN pip install --find-links=/wheels/small --find-links=/wheels/basic --find-links=/wheels/langchain --find-links=/wheels/heavy /wheels/heavy/*.whl && \
    rm -rf /wheels

# Create posey-agents user and group
RUN groupadd -r posey-agents && useradd -r -g posey-agents posey-agents

# Create necessary directories and set permissions
RUN mkdir -p /app/models /app/data && \
    mkdir -p /app/service/scripts && \
    chown -R posey-agents:posey-agents /app

# Copy scripts first (change less frequently)
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    chown posey-agents:posey-agents /app/entrypoint.sh

# Copy application code (changes most frequently)
COPY . /app/service/

# Switch to non-root user
USER posey-agents

EXPOSE 5555

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5555/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
