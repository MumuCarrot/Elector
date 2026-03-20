# Stage 1: build dependencies
FROM python:3.12-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VENV_PATH=/opt/venv

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && python -m venv $VENV_PATH \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$VENV_PATH/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN sed -i 's/\r$//' /app/start.sh \
    && chmod +x /app/start.sh

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["/bin/sh", "/app/start.sh"]
