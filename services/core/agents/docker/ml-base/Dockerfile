FROM --platform=$BUILDPLATFORM python:3.12-slim

# Set ARG for platform targeting
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building on $BUILDPLATFORM for $TARGETPLATFORM"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=0 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  # Add retry and timeout settings
  PIP_RETRIES=5 \
  PIP_TIMEOUT=200 \
  PIP_DEFAULT_TIMEOUT=200 \
  # Explicitly disable CUDA to prevent hangs
  CUDA_VISIBLE_DEVICES="" \
  TORCH_CUDA_ARCH_LIST="None" \
  USE_CUDA=0

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

# Install PyTorch separately with CPU-only version to avoid CUDA issues
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu --verbose || (echo "Failed to install PyTorch CPU version" && exit 1)

# Install transformers libraries
RUN grep "^transformers\|^sentence-transformers" ml-requirements.txt | xargs pip install --no-cache-dir --verbose || (echo "Failed to install transformer libraries" && exit 1)

# Install LangChain packages
RUN grep "^langchain" ml-requirements.txt | xargs pip install --no-cache-dir --verbose || (echo "Failed to install LangChain packages" && exit 1)

# Install Auth packages separately
RUN echo "--- Installing Auth packages ---" && \
  pip install --no-cache-dir PyJWT==2.8.0 supertokens-python==0.19.0 --verbose && \
  echo \"------------------------------\"\n

# Install all remaining packages (except explicitly handled ones)
# Filter out auth packages, comments (#), and the specific comment line marker
RUN cat ml-requirements.txt | grep -v \"^#\|^torch\|^transformers\|^sentence-transformers\|^langchain\|^numpy\|^pandas\|^scipy\|^PyJWT\|^supertokens-python\|# -->\" | grep -v \"^\\s*$\" | xargs -r pip install --no-cache-dir --verbose || (echo 'Failed to install remaining ML packages' && exit 1)

# Verify that installation succeeded
RUN python -c \"import torch; import transformers; import langchain; import jwt; import supertokens_python; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('Transformers version:', transformers.__version__); print('PyJWT version:', jwt.__version__); print(\'SuperTokens version:\', supertokens_python.VERSION); print('ML dependencies installed successfully')\"

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