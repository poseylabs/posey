FROM python:3.12-slim AS builder

WORKDIR /src

COPY requirements.txt .

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
  wget \
  gnupg \
  && rm -rf /var/lib/apt/lists/*

# Copy wheels and install dependencies
COPY --from=builder /wheels /wheels
RUN pip install /wheels/* \
  && rm -rf /wheels

# Install Playwright with Chromium using a more reliable approach
# Set Playwright skip browser download env var and install separately
ENV PLAYWRIGHT_BROWSERS_PATH=/home/voyager/.cache/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Install browser dependencies first as root before switching to non-root user
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  libx11-xcb1 \
  libxcb-dri3-0 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxi6 \
  libxtst6 \
  libnss3 \
  libcups2 \
  libxss1 \
  libxrandr2 \
  libasound2 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgtk-3-0 \
  libgbm1 \
  && rm -rf /var/lib/apt/lists/*

# Since we're using a non-root user, make the directory now
RUN mkdir -p ${PLAYWRIGHT_BROWSERS_PATH} && \
  chown -R voyager:voyager ${PLAYWRIGHT_BROWSERS_PATH}

# Copy application code - recursive copy to include subdirectories
COPY src/ /src/
RUN chown -R voyager:voyager /src

# Switch to non-root user
USER voyager

# Download Chromium without using --with-deps since we installed deps manually
RUN python -m playwright install chromium || \
  python -m playwright install chromium || \
  python -m playwright install chromium

EXPOSE 7777

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:7777/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7777", "--reload"]
