FROM python:3.12-slim AS builder

WORKDIR /app

# Copy requirements first to maximize cache hits
COPY requirements.txt .

# Split requirements into smaller groups for better layer caching
RUN grep -v "langchain\|transformers\|torch\|huggingface\|sentence-transformers\|pydantic\|numpy\|pandas" requirements.txt > small_requirements.txt && \
    grep "pydantic\|numpy\|pandas" requirements.txt > basic_ai_requirements.txt && \
    grep "langchain" requirements.txt > langchain_requirements.txt && \
    grep "transformers\|torch\|huggingface\|sentence-transformers" requirements.txt > heavy_ai_requirements.txt

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN pip install --upgrade pip && \
    pip install wheel

# Create wheel directories
RUN mkdir -p /wheels/small /wheels/basic /wheels/langchain /wheels/heavy

# Install requirements in order of change frequency (least to most frequent)
# Small libraries first (rarely change)
RUN pip wheel --wheel-dir=/wheels/small --find-links=/wheels/small --no-cache-dir -r small_requirements.txt

# Basic AI libraries next (occasionally change)
RUN pip wheel --wheel-dir=/wheels/basic --find-links=/wheels/small --find-links=/wheels/basic --no-cache-dir -r basic_ai_requirements.txt

# Langchain (more frequent updates)
RUN pip wheel --wheel-dir=/wheels/langchain --find-links=/wheels/small --find-links=/wheels/basic --find-links=/wheels/langchain --no-cache-dir -r langchain_requirements.txt

# Heavy AI libraries last (most frequent updates)
RUN pip wheel --wheel-dir=/wheels/heavy --find-links=/wheels/small --find-links=/wheels/basic --find-links=/wheels/langchain --find-links=/wheels/heavy --no-cache-dir -r heavy_ai_requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app/service

# Install production system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    libmagic1 \
    postgresql-server-dev-all \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install in order with specific dependencies first
COPY --from=builder /wheels/small /wheels/small
RUN pip install --no-cache-dir /wheels/small/*.whl

COPY --from=builder /wheels/basic /wheels/basic
RUN pip install --find-links=/wheels/small --no-cache-dir /wheels/basic/*.whl

COPY --from=builder /wheels/langchain /wheels/langchain
RUN pip install --find-links=/wheels/small --find-links=/wheels/basic --no-cache-dir /wheels/langchain/*.whl

COPY --from=builder /wheels/heavy /wheels/heavy
RUN pip install --find-links=/wheels/small --find-links=/wheels/basic --find-links=/wheels/langchain --no-cache-dir /wheels/heavy/*.whl

# Clean up wheels after installation
RUN rm -rf /wheels

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
