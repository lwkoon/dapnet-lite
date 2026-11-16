# --- web UI build ---------------------------------------------------------------
FROM node:20-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# --- runtime ----------------------------------------------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DAPNET_SETTINGS=/data/Settings.json \
    DAPNET_STATE_FILE=/data/State.json \
    DAPNET_WEB_DIR=/app/web \
    DAPNET_HTTP_PORT=8080 \
    DAPNET_TX_PORT=43434
WORKDIR /app
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir "starlette>=0.46" "uvicorn>=0.34"
COPY backend/dapnet ./dapnet
COPY --from=web /web/dist ./web
RUN useradd --system --uid 10001 --home /data dapnet && mkdir -p /data && chown dapnet /data
USER dapnet
VOLUME ["/data"]
EXPOSE 8080 43434
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request,os;urllib.request.urlopen('http://127.0.0.1:%s/api/core/version' % os.environ['DAPNET_HTTP_PORT'], timeout=4)"
CMD ["python", "-m", "dapnet"]
