FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "fastapi>=0.116,<1" "uvicorn[standard]>=0.35,<1"
RUN useradd --system --uid 10001 nexus && mkdir -p /data && chown -R nexus:nogroup /data /app
ENV NEXUS_STATE_DB=/data/state.db \
    NEXUS_CANONICAL_DB=/data/canonical.db \
    NEXUS_VAULT_ROOT=/data/nexus_vault \
    NEXUS_DATA_DIR=/data \
    NEXUS_AUTH_REQUIRED=1 \
    PORT=8421
EXPOSE 8421
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ['PORT'] + '/ready', timeout=3)"
CMD ["sh", "-c", "chown -R nexus:nogroup /data && exec gosu nexus python start.py"]
