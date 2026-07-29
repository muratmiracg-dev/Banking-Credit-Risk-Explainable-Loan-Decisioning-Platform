FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CREDIT_RISK_ROOT=/app

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app --uid 10001 app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY artifacts/model ./artifacts/model
COPY artifacts/metrics/executive_summary.json ./artifacts/metrics/executive_summary.json

RUN pip install --no-cache-dir .

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"

CMD ["uvicorn", "credit_risk.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
