from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "medflow",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.vlm_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    result_expires=3600,  # 1 hour
)

if __name__ == '__main__':
    celery_app.start()

