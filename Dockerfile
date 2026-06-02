FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    curl \
    && python -m venv "$VIRTUAL_ENV" \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser && \
    mkdir -p /app/vivu_backend/staticfiles /app/vivu_backend/media /app/vector_db_data && \
    chown -R appuser:appuser /app

USER appuser

ENV DATABASE_ENGINE=django.db.backends.sqlite3 \
    SQLITE_DB_PATH=/tmp/docker-build.sqlite3 \
    CHROMA_PERSIST_DIRECTORY=vector_db_data \
    DJANGO_STATICFILES_STORAGE=whitenoise.storage.CompressedStaticFilesStorage \
    REDIS_HOST=localhost \
    REDIS_PORT=6379 \
    REDIS_DB=0

RUN python vivu_backend/manage.py collectstatic --noinput

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgomp1 \
    curl \
    && addgroup --system appuser \
    && adduser --system --ingroup appuser appuser \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=appuser:appuser /app /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python vivu_backend/manage.py migrate --noinput && python vivu_backend/manage.py runserver 0.0.0.0:8000"]
