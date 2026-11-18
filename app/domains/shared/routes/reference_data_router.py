from fastapi import APIRouter

from app.domains.auth.utils import get_countries
from app.domains.shared.constants import HEAR_ABOUT_ASRP_OPTIONS


router = APIRouter(prefix="", tags=["Reference data"])


@router.get(
    "/feedback-additional-info/hear-about-options",
    summary="List available hear-about options",
    status_code=200,
)
async def get_hear_about_options() -> list[dict[str, str]]:
    return list(HEAR_ABOUT_ASRP_OPTIONS)


@router.get(
    "/auth/countries",
    summary="List available countries",
    status_code=200,
)
async def countries_list() -> list[dict]:
    return get_countries()
