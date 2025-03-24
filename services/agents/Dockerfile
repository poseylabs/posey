FROM python:3.12-slim AS builder

WORKDIR /app

# Copy requirements first to maximize cache hits
COPY requirements.txt .

# Split requirements into separate layers for better caching
RUN grep -v "langchain\|transformers\|torch\|huggingface\|sentence-transformers" requirements.txt > core_requirements.txt && \
    grep "langchain\|transformers\|torch\|huggingface\|sentence-transformers" requirements.txt > ai_requirements.txt

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

# Install core requirements first (these change less frequently)
RUN mkdir -p /wheels/core && \
    pip wheel --only-binary :all: -r core_requirements.txt -w /wheels/core

# Install AI requirements (these change more frequently)
RUN mkdir -p /wheels/ai && \
    pip wheel --only-binary :all: -r ai_requirements.txt -w /wheels/ai

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

# Copy wheels and install dependencies in stages to avoid space issues
COPY --from=builder /wheels/core /wheels/core
RUN pip install --no-cache-dir /wheels/core/* && rm -rf /wheels/core

COPY --from=builder /wheels/ai /wheels/ai
RUN pip install --no-cache-dir /wheels/ai/* && rm -rf /wheels/ai

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
