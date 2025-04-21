# Use the correct base image tag
ARG BASE_IMAGE_TAG=docker.io/poseylabs/posey-agents-ml-base:latest

# --- Stage 1: Export dependencies using Poetry --- #
FROM python:3.12-slim AS exporter

# Install poetry
RUN pip install poetry==1.8.3 # Pin poetry version for consistency

WORKDIR /tmp

# Copy only the files needed for dependency resolution/export
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt
# --without-hashes is recommended for compatibility
# --only main includes only main dependencies (no dev group)
RUN poetry export --without-hashes --only main -o requirements.txt

# --- Stage 2: Build the final agent image --- #
FROM ${BASE_IMAGE_TAG}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy generated requirements.txt from the exporter stage
COPY --from=exporter /tmp/requirements.txt .

# ---> SIMPLIFIED: Directly install requirements from generated file <--- 
# No more wheel building stage
RUN echo "--- Installing agent requirements from generated requirements.txt ---" && \
    pip install --no-cache-dir -r requirements.txt --verbose && \
    echo "---------------------------------------------------------------------"

# ---> ADDED: Check installed packages after direct install <--- 
RUN echo "--- Installed packages after agent pip install: ---" && pip freeze && echo "---------------------------------------------------"

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

# Install the local posey-agents package using its pyproject.toml
# This registers the entry points defined within it.
RUN echo "--- Installing local posey-agents package ---" && \
    pip install --no-cache-dir /app/service/ && \
    echo "-------------------------------------------"

RUN echo "--- Installed packages after LOCAL package install: ---" && pip freeze && echo "---------------------------------------------------"

# Switch to non-root user
USER posey-agents

EXPOSE 5555

ENTRYPOINT ["/app/entrypoint.sh"]
