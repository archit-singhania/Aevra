FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*
COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/aevra_api ./aevra_api
RUN pip install --no-cache-dir .
COPY alembic.ini ./alembic.ini
COPY infrastructure/migrations ./infrastructure/migrations
EXPOSE 8000
CMD ["uvicorn", "aevra_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
