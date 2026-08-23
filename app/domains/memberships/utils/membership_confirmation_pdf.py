from datetime import datetime, timezone

from app.core.pdf.renderer import PdfTemplateRenderer
from app.domains.memberships.schemas.user_memberships import MembershipConfirmationSchema


MEMBERSHIP_CONFIRMATION_TEMPLATE = "domains/memberships/templates/pdf/membership_confirmation.html"


def render_membership_confirmation_pdf(
    confirmation: MembershipConfirmationSchema,
    renderer: PdfTemplateRenderer,
    issued_at: datetime | None = None,
) -> bytes:
    issued_at = issued_at or datetime.now(timezone.utc)
    return renderer.render(
        MEMBERSHIP_CONFIRMATION_TEMPLATE,
        {
            "member_name": confirmation.member_name,
            "membership_type": confirmation.membership_type.value,
            "membership_id": confirmation.membership_id,
            "valid_through": _format_date(confirmation.valid_through),
            "issued_on": _format_date(issued_at),
        },
    )


def _format_date(value: datetime) -> str:
    return value.strftime("%B %d, %Y")
