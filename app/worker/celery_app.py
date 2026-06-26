from celery import Celery
from app.core.config import settings

# initialization
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,#from whom to take task
    backend=settings.REDIS_URL#after done whom to report
)

# JSON serialization (safer for complex data -prevents code injection attacks)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# tell Celery where to look for the actual bg jobs
celery_app.autodiscover_tasks(["app.worker.tasks"])