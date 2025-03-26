FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=0 \
  PIP_DISABLE_PIP_VERSION_CHECK=1

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

# Install all ML dependencies from the requirements file
RUN pip install --no-cache-dir -r ml-requirements.txt

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