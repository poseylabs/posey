FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=0 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  # Add retry and timeout settings
  PIP_RETRIES=5 \
  PIP_TIMEOUT=200 \
  PIP_DEFAULT_TIMEOUT=200

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  g++ \
  make \
  cmake \
  libc6-dev \
  libpq-dev \
  git \
  curl \
  ca-certificates \
  libmagic1 \
  postgresql-client \
  postgresql-server-dev-all \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel setuptools

# Create a directory for the requirements files
WORKDIR /tmp/build

# Copy only the requirements file for heavy ML dependencies
COPY ml-requirements.txt .

# Print system resources for debugging
RUN echo "=== System Resources ===" && \
  free -h || echo "free command not available" && \
  df -h && \
  echo "=== Installing ML dependencies ==="

# Install ML dependencies in batches for better error handling and to prevent timeout
# First install core numerical packages
RUN pip install --no-cache-dir numpy pandas scipy --verbose || (echo "Failed to install core numerical packages" && exit 1)

# Install PyTorch separately to isolate potential issues
RUN grep "^torch" ml-requirements.txt | xargs pip install --no-cache-dir --verbose || (echo "Failed to install PyTorch" && exit 1)

# Install transformers libraries
RUN grep "^transformers\|^sentence-transformers" ml-requirements.txt | xargs pip install --no-cache-dir --verbose || (echo "Failed to install transformer libraries" && exit 1)

# Install LangChain packages
RUN grep "^langchain" ml-requirements.txt | xargs pip install --no-cache-dir --verbose || (echo "Failed to install LangChain packages" && exit 1)

# Install all remaining packages
RUN cat ml-requirements.txt | grep -v "^torch\|^transformers\|^sentence-transformers\|^langchain\|^numpy\|^pandas\|^scipy" | xargs pip install --no-cache-dir --verbose || (echo "Failed to install remaining ML packages" && exit 1)

# Verify that installation succeeded
RUN python -c "import torch; import transformers; import langchain; print('PyTorch version:', torch.__version__); print('Transformers version:', transformers.__version__); print('ML dependencies installed successfully')"

# Clean up build files
RUN rm -rf /tmp/build

# Set the working directory for derived images
WORKDIR /app

# Create a non-root user for derived images
RUN groupadd -r posey-agents && useradd -r -g posey-agents posey-agents && \
  mkdir -p /app && \
  chown -R posey-agents:posey-agents /app

# Label the image
LABEL org.opencontainers.image.description="Posey Agents ML Base Image with PyTorch, Transformers, and other heavy dependencies pre-installed"
LABEL org.opencontainers.image.source="https://github.com/posey/posey" 