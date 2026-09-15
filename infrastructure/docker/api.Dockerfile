FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/aevra_api ./aevra_api
COPY alembic.ini ./alembic.ini
COPY infrastructure/migrations ./infrastructure/migrations
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["uvicorn", "aevra_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
