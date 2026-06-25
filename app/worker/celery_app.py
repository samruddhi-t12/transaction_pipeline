from celery import Celery
from app.core.config import settings

# Initialize Celery and tell it to use Redis as the message broker
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Optional: Configure Celery for JSON serialization (safer for complex data)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Tell Celery where to look for the actual background jobs
celery_app.autodiscover_tasks(["app.worker.tasks"])