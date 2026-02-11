from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.users.exceptions import ResidencyNotFoundError, UserNotFoundError
from app.domains.users.schemas import ResidencyViewSchema
from app.domains.users.services import ResidencyServiceDep

router = APIRouter(prefix="/users/{user_id}/residencies", tags=["Residency"])


class GetUserResidencies(Responses):
    USER_NOT_FOUND = 404, "User with proved ID not found"


@router.get(
    "",
    responses=GetUserResidencies.responses,
    summary="Get user residencies",
)
async def get_user_residencies(
    user_id: int,
    service: ResidencyServiceDep,
) -> list[ResidencyViewSchema]:
    try:
        user_residencies = await service.get_by_user_id(user_id)
        return [ResidencyViewSchema.model_validate(residency) for residency in user_residencies]
    except UserNotFoundError:
        raise GetUserResidencies.USER_NOT_FOUND


class GetSingleUserResidency(GetUserResidencies):
    RESIDENCY_NOT_FOUND = 404, "Residency with proved ID not found"


@router.get(
    "/{residency_id}",
    summary="Get user residency by residency ID",
)
async def get_single_user_residency(
    user_id: int,
    residency_id: int,
    service: ResidencyServiceDep,
) -> ResidencyViewSchema:
    try:
        user_residency = await service.get_user_residency_by_id(user_id=user_id, residency_id=residency_id)
        return ResidencyViewSchema.model_validate(user_residency)

    except UserNotFoundError:
        raise GetSingleUserResidency.USER_NOT_FOUND

    except ResidencyNotFoundError:
        raise GetSingleUserResidency.RESIDENCY_NOT_FOUND
