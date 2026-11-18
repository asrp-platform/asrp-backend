from app.domains.emails.tasks import send_email_task


class EmailQueue:
    @staticmethod
    def send_email(
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

    @staticmethod
    def send_mailing(emails_to: list[str], subject, body: str):
        for email in emails_to:
            send_email_task.apply_async(
                kwargs={
                    "to": email,
                    "subject": subject,
                    "body": body,
                },
                queue="emails",
            )
