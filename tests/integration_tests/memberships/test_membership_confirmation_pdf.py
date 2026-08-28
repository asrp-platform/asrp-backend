from datetime import datetime, timedelta, timezone
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import BASE_DIR
from app.domains.memberships.schemas.user_memberships import (
    MembershipConfirmationReportSchema,
    MembershipHistoryEventSchema,
    MembershipHistoryEventTypeEnum,
    MembershipStatusEnum,
)
from app.domains.memberships.utils.membership_confirmation_pdf import render_membership_confirmation_pdf


class HtmlTemplateRenderer:
    def __init__(self):
        self.__environment = Environment(
            loader=FileSystemLoader(BASE_DIR / "app"),
            autoescape=select_autoescape(("html", "xml")),
        )

    def render(self, template_name: str, context: dict[str, Any]) -> bytes:
        return self.__environment.get_template(template_name).render(**context).encode()


def test_membership_confirmation_template_renders_non_active_status_and_history() -> None:
    issued_at = datetime(2026, 8, 28, tzinfo=timezone.utc)
    report = MembershipConfirmationReportSchema(
        member_name="Example Member",
        membership_type="Full Member",
        membership_id="ASRP-2026-00001",
        status=MembershipStatusEnum.TERMINATED,
        member_since=issued_at - timedelta(days=365),
        valid_through=issued_at - timedelta(days=1),
        issued_at=issued_at,
        history=[
            MembershipHistoryEventSchema(
                event_type=MembershipHistoryEventTypeEnum.ACTIVATED,
                occurred_at=issued_at - timedelta(days=365),
                membership_type="Full Member",
            ),
            MembershipHistoryEventSchema(
                event_type=MembershipHistoryEventTypeEnum.TERMINATED,
                occurred_at=issued_at - timedelta(days=1),
                reason="Membership terminated",
            ),
        ],
    )

    html = render_membership_confirmation_pdf(report, HtmlTemplateRenderer()).decode()

    assert "Status:</span> <span class=\"status\">Terminated</span>" in html
    assert "Available membership history" in html
    assert "Membership activated" in html
    assert "Membership terminated" in html
    assert "Reason: Membership terminated" in html
    assert "is an active member" not in html
    assert "confirms the membership record and current status" in html
