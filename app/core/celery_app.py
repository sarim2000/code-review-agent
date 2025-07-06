"""Celery application configuration"""
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Celery configuration
celery_app = Celery(
    "code_review_agent",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["app.tasks.analysis_tasks"]
)

# Celery configuration settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Improved error handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    result_expires=3600,  # 1 hour
    # Better exception serialization
    task_send_sent_event=True,
)