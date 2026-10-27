"""
Celery application factory for ContentIQ.
Broker: Redis (REDIS_URL env var).
Result backend: Redis.

Usage:
  Start worker:  celery -A app.workers.celery_app worker --loglevel=info -Q media
  Flower monitor: celery -A app.workers.celery_app flower
"""
from __future__ import annotations

import os
from celery import Celery  # type: ignore

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "contentiq",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks.media_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          # re-queue if worker crashes mid-task
    worker_prefetch_multiplier=1, # process one task at a time per worker slot
    result_expires=86400,         # keep results for 24h
    task_routes={
        "app.workers.tasks.media_tasks.*": {"queue": "media"},
    },
)
