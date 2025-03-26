FROM registry.digitalocean.com/posey/agents-ml-base:latest AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Accept build arguments for flexible caching
ARG BUILDKIT_INLINE_CACHE=1
ARG PIP_CACHE_DIR=/pip-cache

WORKDIR /app

# Copy requirements file - already filtered to exclude base image dependencies
COPY requirements.txt .

# Create wheel directory
RUN mkdir -p /wheels

# Build wheels for requirements with parallel installation
RUN pip wheel --wheel-dir=/wheels -r requirements.txt -j 4

# Final production stage - also using the ML base image
FROM registry.digitalocean.com/posey/agents-ml-base:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/service

WORKDIR /app

# Copy wheels from builder and install with parallel processing
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*.whl -j 4 && \
    rm -rf /wheels

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
