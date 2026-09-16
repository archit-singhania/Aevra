# Workers

Celery jobs, retries, idempotency, scheduled execution, and publish verification live in
`celery_app.py` and `tasks.py`. The worker uses Redis as a free/local broker and Celery's
backoff+jitter retry policy. LangGraph is not used as the durable job scheduler.
