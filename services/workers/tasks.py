"""Retry-safe worker task declarations.

The task bodies intentionally delegate to application services. No provider
credentials or prompt state is kept in Celery payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aevra_api.config import get_settings
from aevra_api.db.models import ScheduledPost
from aevra_api.db.session import SessionLocal
from aevra_api.domain.errors import DomainError
from aevra_api.publishing.contracts import PublisherError
from aevra_api.schemas.publishing import PublishRequest
from aevra_api.services.publishing import PublishingService

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
def dispatch_due_posts(_task_instance: Any) -> dict[str, str | int]:
    """Claim and publish due scheduled posts idempotently."""
    session = SessionLocal()
    processed = 0
    try:
        due = list(
            session.query(ScheduledPost)
            .filter(
                ScheduledPost.status == "scheduled",
                ScheduledPost.scheduled_for <= datetime.now(UTC),
            )
            .order_by(ScheduledPost.scheduled_for)
            .limit(25)
            .all()
        )
        for item in due:
            item.status = "processing"
            item.attempts += 1
            session.commit()
            payload = item.payload if isinstance(item.payload, dict) else {}
            try:
                job = PublishingService(session, get_settings()).publish(
                    item.created_by_user_id,
                    item.workspace_id,
                    PublishRequest(
                        campaign_id=item.campaign_id,
                        social_account_id=item.social_account_id,
                        idempotency_key=f"scheduled:{item.idempotency_key}",
                        text=str(payload.get("text", "")),
                        media_urls=[str(url) for url in payload.get("media_urls", [])],
                    ),
                )
                item.published_job_id = job.id
                item.status = "published" if job.status in {"published", "verified"} else "failed"
                item.error_message = job.error_message
            except (DomainError, PublisherError, TimeoutError, ConnectionError, ValueError) as error:
                item.status = "failed"
                item.error_message = str(error)[:1000]
            session.commit()
            processed += 1
        return {"status": "completed", "job": "dispatch_due_posts", "processed": processed}
    finally:
        session.close()


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
