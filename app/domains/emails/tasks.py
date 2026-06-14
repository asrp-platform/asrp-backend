import asyncio

from app.core.celery import celery_app
from app.domains.emails.providers.gmail import GmailProvider
from app.domains.emails.services import get_email_service


@celery_app.task(
    name="emails.send_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_email_task(to: str, subject: str, body: str) -> None:
    email_service = get_email_service(GmailProvider)

    asyncio.run(
        email_service.send_email(
            to=to,
            subject=subject,
            body=body,
        )
    )
