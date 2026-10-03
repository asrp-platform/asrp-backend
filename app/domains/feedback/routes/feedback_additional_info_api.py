from fastapi import APIRouter

from app.domains.feedback.use_cases import GetHearAboutOptionsUseCaseDep


router = APIRouter(prefix="/feedback-additional-info", tags=["Feedback Additional Info"])


@router.get(
    "/hear-about-options",
    summary="List available hear-about options",
    status_code=200,
)
async def get_hear_about_options(use_case: GetHearAboutOptionsUseCaseDep) -> tuple[str, ...]:
    return await use_case.execute()
