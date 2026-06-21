from typing import Annotated

from fastapi import Depends

from app.domains.emails.tasks import send_email_task


class EmailQueue:
    @classmethod
    async def send_email(
        cls,
        to: str,
        subject: str,
        body: str,
    ) -> None:
        send_email_task.apply_async(
            kwargs={
                "to": to,
                "subject": subject,
                "body": body,
            },
            queue="emails",
        )


EmailQueueDep = Annotated[EmailQueue, Depends(EmailQueue)]
