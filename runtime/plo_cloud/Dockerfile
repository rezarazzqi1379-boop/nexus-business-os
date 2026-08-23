FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NEXUS_PLO_DB=/data/nexus_plo.db
WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir 'psycopg[binary]>=3.2,<4' \
 && python -m compileall -q . \
 && python tests/test_cloud.py
VOLUME ["/data"]
CMD ["python","worker.py","--db","/data/nexus_plo.db"]
