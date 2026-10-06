from fastapi import APIRouter

from app.domains.shared.constants import HEAR_ABOUT_ASRP_OPTIONS


router = APIRouter(prefix="", tags=["Reference data"])


@router.get(
    "/feedback-additional-info/hear-about-options",
    summary="List available hear-about options",
    status_code=200,
)
async def get_hear_about_options() -> tuple[str, ...]:
    return HEAR_ABOUT_ASRP_OPTIONS
