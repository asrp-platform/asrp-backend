from celery import Celery
from kombu import Queue

from app.core.config import DB_URL, settings


celery_app = Celery(
    "app",
    broker=settings.celery_broker_url,
    include=[
        "app.domains.emails.tasks",
    ],
    backend=DB_URL,
)

celery_app.conf.task_queues = (Queue("emails", durable=True),)
celery_app.conf.task_routes = {
    "emails.send_email": {"queue": "emails"},
}
celery_app.conf.task_default_delivery_mode = "persistent"
celery_app.conf.update(
    task_track_started=True,
    result_extended=True,
    result_expires=86400,
)
