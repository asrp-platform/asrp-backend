from fastapi import APIRouter
from pydantic import BaseModel

from app.domains.emails.email_queue import EmailQueue


router = APIRouter(prefix="/emails", tags=["Admin: Emails"])


class TestMailingSchema(BaseModel):
    subject: str
    body: str


@router.post(
    "/test-mailing",
    status_code=202,
    summary="Send a test mailing",
)
def send_test_mailing(body: TestMailingSchema) -> dict[str, int]:
    to_emails: list[str] = ["maxevg72@gmail.com", "maxevg12@gmail.com"]
    EmailQueue.send_mailing(
        emails_to=to_emails,
        subject=body.subject,
        body=body.body,
    )
    return {"recipients_count": len(to_emails)}
