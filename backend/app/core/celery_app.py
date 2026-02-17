"""
EduCore Backend - Celery Application Configuration
Background task processing with Redis broker
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery application
celery_app = Celery(
    "edusms",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "app.tasks.notifications",
        "app.tasks.reports",
        "app.tasks.scheduled",
        "app.tasks.analytics",
    ],
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes

    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Task routing
    task_routes={
        "app.tasks.notifications.*": {"queue": "notifications"},
        "app.tasks.reports.*": {"queue": "reports"},
        "app.tasks.scheduled.*": {"queue": "scheduled"},
        "app.tasks.analytics.*": {"queue": "analytics"},
    },

    # Beat scheduler for periodic tasks
    beat_schedule={
        # Daily tasks
        "daily-attendance-report": {
            "task": "app.tasks.scheduled.generate_daily_attendance_report",
            "schedule": crontab(hour=6, minute=0),  # 6 AM UTC
        },
        "check-overdue-fees": {
            "task": "app.tasks.scheduled.check_overdue_fees",
            "schedule": crontab(hour=7, minute=0),  # 7 AM UTC
        },
        "send-fee-reminders": {
            "task": "app.tasks.scheduled.send_fee_reminders",
            "schedule": crontab(hour=8, minute=0, day_of_week="mon"),  # Monday 8 AM
        },

        # Hourly tasks
        "cleanup-expired-sessions": {
            "task": "app.tasks.scheduled.cleanup_expired_sessions",
            "schedule": crontab(minute=0),  # Every hour
        },

        # Weekly tasks
        "weekly-analytics-rollup": {
            "task": "app.tasks.analytics.weekly_rollup",
            "schedule": crontab(hour=2, minute=0, day_of_week="sun"),  # Sunday 2 AM
        },
        "generate-risk-predictions": {
            "task": "app.tasks.analytics.generate_risk_predictions",
            "schedule": crontab(hour=3, minute=0, day_of_week="sun"),  # Sunday 3 AM
        },
    },
)

# For testing without Redis
if settings.CELERY_TASK_ALWAYS_EAGER:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
