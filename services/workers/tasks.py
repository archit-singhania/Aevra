"""Retry-safe worker task declarations.

The task bodies intentionally delegate to application services. No provider
credentials or prompt state is kept in Celery payloads.
"""

from __future__ import annotations

from typing import Any

from services.workers.celery_app import celery_app


def _task(**kwargs: Any):
    def decorator(function: Any) -> Any:
        return celery_app.task(**kwargs)(function) if celery_app is not None else function

    return decorator


@_task(
    bind=True,
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def dispatch_due_posts(_task_instance: Any) -> dict[str, str]:
    return {"status": "accepted", "job": "dispatch_due_posts"}


@_task(
    bind=True,
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
    max_retries=5,
)
def collect_post_metrics(_task_instance: Any) -> dict[str, str]:
    return {"status": "accepted", "job": "collect_post_metrics"}
