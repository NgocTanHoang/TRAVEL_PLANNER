FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUSERBASE=/opt/python-deps \
    PATH="/opt/python-deps/bin:$PATH"

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /build/requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user -r /build/requirements.txt

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUSERBASE=/opt/python-deps \
    PATH="/opt/python-deps/bin:$PATH" \
    PYTHONPATH="/opt/python-deps/lib/python3.11/site-packages"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appuser \
    && adduser --system --ingroup appuser appuser

COPY --from=builder /opt/python-deps /opt/python-deps
COPY --chown=appuser:appuser requirements.txt /app/requirements.txt
COPY --chown=appuser:appuser vivu_backend /app/vivu_backend
COPY --chown=appuser:appuser vivu_frontend /app/vivu_frontend
COPY --chown=appuser:appuser vivu_scraper /app/vivu_scraper

RUN mkdir -p /app/vivu_backend/staticfiles /app/vivu_backend/media /app/vector_db_data /app/vivu_scraper/outputs && \
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

EXPOSE 8000

CMD ["sh", "-c", "python vivu_backend/manage.py migrate --noinput && python vivu_backend/manage.py runserver 0.0.0.0:8000"]
