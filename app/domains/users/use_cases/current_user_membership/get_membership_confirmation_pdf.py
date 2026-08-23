from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.core.pdf.renderer import PdfTemplateRendererDep
from app.domains.memberships.utils.membership_confirmation_pdf import render_membership_confirmation_pdf
from app.domains.users.models import User
from app.domains.users.use_cases.current_user_membership.get_membership_confirmation import (
    GetMembershipConfirmationUseCaseDep,
)


@dataclass(frozen=True)
class MembershipConfirmationPdf:
    content: bytes
    filename: str


class GetMembershipConfirmationPdfUseCase:
    def __init__(
        self,
        confirmation_use_case: GetMembershipConfirmationUseCaseDep,
        pdf_renderer: PdfTemplateRendererDep,
    ):
        self.__confirmation_use_case = confirmation_use_case
        self.__pdf_renderer = pdf_renderer

    async def execute(self, current_user: User) -> MembershipConfirmationPdf:
        confirmation = await self.__confirmation_use_case.execute(current_user)
        return MembershipConfirmationPdf(
            content=render_membership_confirmation_pdf(confirmation, self.__pdf_renderer),
            filename=f"membership-confirmation-{confirmation.membership_id}.pdf",
        )


GetMembershipConfirmationPdfUseCaseDep = Annotated[
    GetMembershipConfirmationPdfUseCase, Depends(GetMembershipConfirmationPdfUseCase)
]
