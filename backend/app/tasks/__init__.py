"""
EduCore Backend - Background Tasks Package
Contains Celery tasks for async processing
"""
from app.core.celery_app import celery_app

__all__ = ["celery_app"]
