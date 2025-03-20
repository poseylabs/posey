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
    && pip wheel --only-binary :all: -r requirements.txt -w /wheels \
    && rm -rf /var/lib/apt/lists/*

# Production stage
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app/service

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    libmagic1 \
    postgresql-server-dev-all \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install dependencies
COPY --from=builder /wheels /wheels
RUN pip install /wheels/* \
    && rm -rf /wheels

# Create posey-agents user and group
RUN groupadd -r posey-agents && useradd -r -g posey-agents posey-agents

# Create necessary directories and set permissions
RUN mkdir -p /app/models /app/data && \
    mkdir -p /app/service/scripts && \
    chown -R posey-agents:posey-agents /app

# Copy application code
COPY . /app/service/
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
RUN chown posey-agents:posey-agents /app/entrypoint.sh

# Switch to non-root user
USER posey-agents

EXPOSE 5555

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5555/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
