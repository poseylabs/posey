# Use the correct base image tag
ARG BASE_IMAGE_TAG=docker.io/poseylabs/posey-agents-ml-base:latest
FROM ${BASE_IMAGE_TAG}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# ---> SIMPLIFIED: Directly install requirements <--- 
# No more wheel building stage
RUN echo "--- Installing agent requirements directly ---" && \
    pip install --no-cache-dir -r requirements.txt --verbose && \
    echo "-------------------------------------------"

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

# Switch to non-root user
USER posey-agents

EXPOSE 5555

ENTRYPOINT ["/app/entrypoint.sh"]
