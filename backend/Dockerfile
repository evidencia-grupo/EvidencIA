FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes --target /dependencies -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN useradd --uid 10001 --create-home appuser
COPY --from=builder /dependencies /usr/local/lib/python3.12/site-packages
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser ml ./ml
USER 10001:10001
ENV PORT=8000 ENVIRONMENT=production ENV=production
EXPOSE 8000
CMD exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
