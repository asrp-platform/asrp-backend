from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.common.exceptions import NotResourceOwnerError
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.exceptions import (
    CannotDeleteLastResidencyError,
    ProfessionalExperienceCurrentPositionExistsError,
    ResidencyNotFoundError,
    UserNotFoundError,
)
from app.domains.users.schemas import ResidencyCreateSchema, ResidencyUpdateSchema, ResidencyViewSchema
from app.domains.users.services import ResidencyServiceDep

router = APIRouter(prefix="/users/{user_id}/residencies", tags=["Residency"])


class GetUserResidenciesResponses(Responses):
    USER_NOT_FOUND = 404, "User with proved ID not found"


@router.get(
    "",
    responses=GetUserResidenciesResponses.responses,
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
        raise GetUserResidenciesResponses.USER_NOT_FOUND


class GetSingleUserResidencyResponses(GetUserResidenciesResponses):
    RESIDENCY_NOT_FOUND = 404, "Residency with proved ID not found"


@router.get(
    "/{residency_id}", summary="Get user residency by residency ID", responses=GetSingleUserResidencyResponses.responses
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
        raise GetSingleUserResidencyResponses.USER_NOT_FOUND

    except ResidencyNotFoundError:
        raise GetSingleUserResidencyResponses.RESIDENCY_NOT_FOUND


class CreateUserResidencyResponses(GetUserResidenciesResponses):
    NOT_RESOURCE_OWNER = 403, "Not resource owner"
    PROFESSIONAL_EXPERIENCE_CURRENT_POSITION_EXISTS = 409, "Current position already exists in professional experience"


@router.post(
    "",
    status_code=201,
    responses=CreateUserResidencyResponses.responses,
    summary="Create a residency for a user",
)
async def create_residency_for_user(
    user_id: int,
    current_user: CurrentUserDep,
    service: ResidencyServiceDep,
    residency_creation_data: ResidencyCreateSchema,
) -> ResidencyViewSchema:
    try:
        user_residency = await service.create_user_residency(
            user_id, current_user.id, **residency_creation_data.model_dump()
        )
        return ResidencyViewSchema.model_validate(user_residency)

    except NotResourceOwnerError:
        raise CreateUserResidencyResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise CreateUserResidencyResponses.USER_NOT_FOUND

    except ProfessionalExperienceCurrentPositionExistsError:
        raise CreateUserResidencyResponses.PROFESSIONAL_EXPERIENCE_CURRENT_POSITION_EXISTS


class UpdateResidencyResponses(CreateUserResidencyResponses):
    pass


@router.put(
    "/{residency_id}",
    responses=UpdateResidencyResponses.responses,
    summary="Update user residency",
)
async def update_user_residency(
    user_id: int,
    residency_id: int,
    current_user: CurrentUserDep,
    service: ResidencyServiceDep,
    residency_update_data: ResidencyUpdateSchema,
) -> ResidencyViewSchema:
    try:
        user_residency = await service.update_user_residency(
            user_id, current_user.id, residency_id, residency_update_data.model_dump()
        )
        return ResidencyViewSchema.model_validate(user_residency)

    except NotResourceOwnerError:
        raise CreateUserResidencyResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise CreateUserResidencyResponses.USER_NOT_FOUND

    except ProfessionalExperienceCurrentPositionExistsError:
        raise UpdateResidencyResponses.PROFESSIONAL_EXPERIENCE_CURRENT_POSITION_EXISTS


class DeleteResidencyResponses(CreateUserResidencyResponses, GetSingleUserResidencyResponses):
    CANNOT_DELETE_LAST_RESIDENCY = 409, "Cannot delete last residency"


@router.delete(
    "/{residency_id}",
    responses=DeleteResidencyResponses.responses,
    summary="Delete user residency",
)
async def delete_user_residency(
    user_id: int,
    residency_id: int,
    current_user: CurrentUserDep,
    service: ResidencyServiceDep,
) -> int:
    try:
        return await service.delete_user_residency(user_id, current_user.id, residency_id)
    except NotResourceOwnerError:
        raise DeleteResidencyResponses.NOT_RESOURCE_OWNER
    except UserNotFoundError:
        raise DeleteResidencyResponses.USER_NOT_FOUND
    except ResidencyNotFoundError:
        raise DeleteResidencyResponses.RESIDENCY_NOT_FOUND
    except CannotDeleteLastResidencyError:
        raise DeleteResidencyResponses.CANNOT_DELETE_LAST_RESIDENCY
