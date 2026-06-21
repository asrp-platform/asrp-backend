from celery import Celery
from kombu import Queue

from app.core.config import settings


celery_app = Celery(
    "app",
    broker=settings.celery_broker_url,
    include=[
        "app.domains.emails.tasks",
    ],
)

celery_app.conf.task_queues = (Queue("emails", durable=True),)

celery_app.conf.task_routes = {
    "emails.send_email": {"queue": "emails"},
}

celery_app.conf.task_default_delivery_mode = "persistent"
