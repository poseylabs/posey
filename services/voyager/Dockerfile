FROM python:3.12-slim AS builder

WORKDIR /src

COPY services/voyager/requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  g++ \
  libc6-dev \
  && pip install --upgrade pip \
  && pip install wheel \
  && pip wheel --only-binary :all: -r requirements.txt -w /wheels \
  && rm -rf /var/lib/apt/lists/*

# Production stage
FROM python:3.12-slim

WORKDIR /src

# Create voyager user and set up directories
RUN useradd -m -d /home/voyager voyager && \
  chown -R voyager:voyager /src && \
  mkdir -p /home/voyager && \
  chown -R voyager:voyager /home/voyager

# Install system dependencies
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy wheels and install dependencies
COPY --from=builder /wheels /wheels
RUN pip install /wheels/* \
  && rm -rf /wheels

# Install Playwright browser
RUN playwright install chromium

# Copy application code
COPY services/voyager/src/* /src/
RUN chown -R voyager:voyager /src

# Switch to non-root user
USER voyager

EXPOSE 7777

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:7777/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7777", "--reload"]
