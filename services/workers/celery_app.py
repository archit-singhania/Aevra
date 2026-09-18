"""Celery application factory; imports Celery lazily for the free API test profile."""

from __future__ import annotations

import os
from typing import Any


def create_celery() -> Any:
    try:
        from celery import Celery  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError("Install the worker extra to run Celery") from error
    app = Celery(
        "aevra",
        broker=os.getenv("AEVRA_REDIS_URL", "redis://localhost:6379/0"),
        backend=os.getenv("AEVRA_REDIS_URL", "redis://localhost:6379/0"),
    )
    app.conf.update(
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_track_started=True,
        beat_schedule={
            "dispatch-due-posts": {
                "task": "services.workers.tasks.dispatch_due_posts",
                "schedule": 30.0,
            },
            "collect-post-metrics": {
                "task": "services.workers.tasks.collect_post_metrics",
                "schedule": 900.0,
            },
            "execute-account-deletions": {
                "task": "services.workers.tasks.execute_account_deletions",
                "schedule": 3600.0,
            },
            "prune-oauth-states": {
                "task": "services.workers.tasks.prune_oauth_states",
                "schedule": 3600.0,
            },
        },
    )
    return app


celery_app = create_celery() if os.getenv("AEVRA_ENABLE_CELERY") == "1" else None
