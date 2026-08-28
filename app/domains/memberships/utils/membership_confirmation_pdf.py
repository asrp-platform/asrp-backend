from datetime import datetime

from app.core.pdf.renderer import PdfTemplateRenderer
from app.domains.memberships.schemas.user_memberships import (
    MembershipConfirmationReportSchema,
    MembershipHistoryEventSchema,
    MembershipHistoryEventTypeEnum,
    MembershipStatusEnum,
)


MEMBERSHIP_CONFIRMATION_TEMPLATE = "domains/memberships/templates/pdf/membership_confirmation.html"


def render_membership_confirmation_pdf(
    report: MembershipConfirmationReportSchema,
    renderer: PdfTemplateRenderer,
) -> bytes:
    return renderer.render(
        MEMBERSHIP_CONFIRMATION_TEMPLATE,
        {
            "member_name": report.member_name,
            "membership_type": report.membership_type,
            "membership_id": report.membership_id,
            "status": report.status.value.title(),
            "member_since": _format_date(report.member_since),
            "valid_through": _format_date(report.valid_through),
            "issued_on": _format_date(report.issued_at),
            "statement": _get_statement(report.status),
            "history": [_history_event_to_context(event) for event in report.history],
        },
    )


def _format_date(value: datetime) -> str:
    return value.strftime("%B %d, %Y")


def _get_statement(status: MembershipStatusEnum) -> str:
    if status == MembershipStatusEnum.ACTIVE:
        return (
            "This document certifies that the individual named above is an active member of the "
            "American Society of Russian-Speaking Pathologists as of the date of issuance."
        )
    return (
        "This document confirms the membership record and current status of the individual named above "
        "as of the date of issuance."
    )


def _history_event_to_context(event: MembershipHistoryEventSchema) -> dict:
    titles = {
        MembershipHistoryEventTypeEnum.ACTIVATED: "Membership activated",
        MembershipHistoryEventTypeEnum.RENEWED: "Membership renewed",
        MembershipHistoryEventTypeEnum.TYPE_CHANGED: "Membership type changed",
        MembershipHistoryEventTypeEnum.SUSPENDED: "Membership suspended",
        MembershipHistoryEventTypeEnum.TERMINATED: "Membership terminated",
    }
    details = []
    if event.previous_membership_type is not None:
        details.append(("Previous membership type", event.previous_membership_type))
    if event.membership_type is not None:
        details.append(("Membership type", event.membership_type))
    if event.previous_valid_through is not None:
        details.append(("Previously valid through", _format_date(event.previous_valid_through)))
    if event.valid_through is not None:
        details.append(("Valid through", _format_date(event.valid_through)))
    if event.suspended_until is not None:
        details.append(("Suspended until", _format_date(event.suspended_until)))
    if event.reason is not None:
        details.append(("Reason", event.reason))
    return {
        "title": titles[event.event_type],
        "occurred_on": _format_date(event.occurred_at),
        "details": details,
    }
