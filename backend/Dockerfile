# Stage 1: build dependencies
FROM python:3.12-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VENV_PATH=/opt/venv

# Minimal build tools for any packages that need compilation
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && python -m venv $VENV_PATH \
    && rm -rf /var/lib/apt/lists/*

# Use the venv's pip
ENV PATH="$VENV_PATH/bin:$PATH"

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: production image
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

 # Copy venv built in the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

RUN if [ ! -f /app/start.sh ]; then \
        echo "ERROR: start.sh not found!" && \
        ls -la /app/ | grep -i start && \
        exit 1; \
    fi && \
    sed -i 's/\r$//' /app/start.sh && \
    chmod +x /app/start.sh && \
    echo "File permissions:" && \
    ls -la /app/start.sh && \
    echo "First line of file:" && \
    head -n 1 /app/start.sh | od -c

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["/bin/sh", "/app/start.sh"]