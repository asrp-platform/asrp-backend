from typing import Annotated

from fastapi import Depends

from app.domains.feedback.schemas import HEAR_ABOUT_ASRP_OPTIONS


class GetHearAboutOptionsUseCase:
    async def execute(self) -> tuple[str, ...]:
        return HEAR_ABOUT_ASRP_OPTIONS


GetHearAboutOptionsUseCaseDep = Annotated[
    GetHearAboutOptionsUseCase,
    Depends(GetHearAboutOptionsUseCase),
]
