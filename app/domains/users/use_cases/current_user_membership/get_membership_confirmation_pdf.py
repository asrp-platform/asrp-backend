import asyncio
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.core.pdf.renderer import PdfTemplateRendererDep
from app.domains.memberships.utils.membership_confirmation_pdf import render_membership_confirmation_pdf
from app.domains.users.models import User
from app.domains.users.use_cases.current_user_membership.get_membership_confirmation_report import (
    GetMembershipConfirmationReportUseCaseDep,
)


@dataclass(frozen=True)
class MembershipConfirmationPdf:
    content: bytes
    filename: str


class GetMembershipConfirmationPdfUseCase:
    def __init__(
        self,
        report_use_case: GetMembershipConfirmationReportUseCaseDep,
        pdf_renderer: PdfTemplateRendererDep,
    ):
        self.__report_use_case = report_use_case
        self.__pdf_renderer = pdf_renderer

    async def execute(self, current_user: User) -> MembershipConfirmationPdf:
        report = await self.__report_use_case.execute(current_user)
        content = await asyncio.to_thread(
            render_membership_confirmation_pdf,
            report,
            self.__pdf_renderer,
        )
        return MembershipConfirmationPdf(
            content=content,
            filename=f"membership-confirmation-{report.membership_id}.pdf",
        )


GetMembershipConfirmationPdfUseCaseDep = Annotated[
    GetMembershipConfirmationPdfUseCase, Depends(GetMembershipConfirmationPdfUseCase)
]
