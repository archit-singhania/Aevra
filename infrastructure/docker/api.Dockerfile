FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*
COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/aevra_api ./aevra_api
COPY services ./services
RUN pip install --no-cache-dir .
COPY alembic.ini ./alembic.ini
COPY infrastructure/migrations ./infrastructure/migrations
COPY infrastructure/docker/api-start.sh ./api-start.sh
RUN chmod +x ./api-start.sh
EXPOSE 10000
CMD ["/app/api-start.sh"]
