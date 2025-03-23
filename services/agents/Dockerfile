FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libpq-dev \
    && pip install --upgrade pip \
    && pip install wheel \
    # Create subdirectories for better organization and smaller image layers
    && mkdir -p /wheels/ai /wheels/core /wheels/db /wheels/utils \
    # Install dependencies in smaller chunks to avoid running out of space
    && grep -v "langchain\|transformers\|torch\|huggingface\|sentence-transformers" requirements.txt > /app/core_requirements.txt \
    && grep "langchain\|transformers\|torch\|huggingface\|sentence-transformers" requirements.txt > /app/ai_requirements.txt \
    # First install core requirements
    && pip wheel --only-binary :all: -r /app/core_requirements.txt -w /wheels/core \
    # Then install AI requirements
    && pip wheel --only-binary :all: -r /app/ai_requirements.txt -w /wheels/ai \
    # Clean up to save space
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /root/.cache

# Production stage
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app/service

# Install curl for healthcheck and other necessary packages
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

# Copy application code
COPY . /app/service/
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    chown posey-agents:posey-agents /app/entrypoint.sh

# Switch to non-root user
USER posey-agents

EXPOSE 5555

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5555/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
