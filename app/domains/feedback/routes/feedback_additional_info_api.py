from fastapi import APIRouter

from app.domains.feedback.constants import HEAR_ABOUT_ASRP_OPTIONS


router = APIRouter(prefix="/feedback-additional-info", tags=["Feedback Additional Info"])


@router.get("/hear-about-options")
async def get_hear_about_options() -> tuple[str, ...]:
    return HEAR_ABOUT_ASRP_OPTIONS
