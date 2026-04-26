from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.shared.deps import CurrentUserDep
from app.domains.users.schemas import (
    FellowshipCreateSchema,
    FellowshipUpdateSchema,
    FellowshipViewSchema,
)
from app.domains.users.services import FellowshipServiceDep

router = APIRouter(
    prefix="/users/{user_id}/fellowships",
    tags=["Fellowship"],
)


class GetUserFellowshipsResponses(Responses):
    USER_NOT_FOUND = 404, "User with proved ID not found"


@router.get(
    "",
    responses=GetUserFellowshipsResponses.responses,
    summary="Get user fellowships",
)
async def get_user_fellowships(
    user_id: int,
    service: FellowshipServiceDep,
) -> list[FellowshipViewSchema]:
    user_fellowships = await service.list_for_user(user_id)
    return [FellowshipViewSchema.model_validate(fellowship) for fellowship in user_fellowships]


class GetSingleUserFellowshipResponses(GetUserFellowshipsResponses):
    FELLOWSHIP_NOT_FOUND = 404, "Fellowship with proved ID not found"


@router.get(
    "/{fellowship_id}",
    responses=GetSingleUserFellowshipResponses.responses,
    summary="Get user fellowship by fellowship ID",
)
async def get_single_user_fellowship(
    user_id: int,
    fellowship_id: int,
    service: FellowshipServiceDep,
) -> FellowshipViewSchema:
    user_fellowship = await service.get_for_user(
        user_id=user_id,
        resource_id=fellowship_id,
    )
    return FellowshipViewSchema.model_validate(user_fellowship)


class CreateUserFellowshipResponses(GetUserFellowshipsResponses):
    NOT_RESOURCE_OWNER = 403, "Not resource owner"
    PROFESSIONAL_EXPERIENCE_CURRENT_POSITION_EXISTS = 409, "Current position already exists in professional experience"


@router.post(
    "",
    status_code=201,
    responses=CreateUserFellowshipResponses.responses,
    summary="Create a fellowship for a user",
)
async def create_fellowship_for_user(
    user_id: int,
    current_user: CurrentUserDep,
    service: FellowshipServiceDep,
    fellowship_creation_data: FellowshipCreateSchema,
) -> FellowshipViewSchema:
    user_fellowship = await service.create_for_user(
        user_id,
        current_user.id,
        **fellowship_creation_data.model_dump(),
    )
    return FellowshipViewSchema.model_validate(user_fellowship)


class UpdateFellowshipResponses(CreateUserFellowshipResponses):
    pass


@router.put(
    "/{fellowship_id}",
    responses=UpdateFellowshipResponses.responses,
    summary="Update user fellowship",
)
async def update_user_fellowship(
    user_id: int,
    fellowship_id: int,
    current_user: CurrentUserDep,
    service: FellowshipServiceDep,
    fellowship_update_data: FellowshipUpdateSchema,
) -> FellowshipViewSchema:
    user_fellowship = await service.update_for_user(
        user_id,
        current_user.id,
        fellowship_id,
        fellowship_update_data.model_dump(),
    )
    return FellowshipViewSchema.model_validate(user_fellowship)


class DeleteFellowshipResponses(
    CreateUserFellowshipResponses,
    GetSingleUserFellowshipResponses,
):
    pass


@router.delete(
    "/{fellowship_id}",
    responses=DeleteFellowshipResponses.responses,
    summary="Delete user fellowship",
)
async def delete_user_fellowship(
    user_id: int,
    fellowship_id: int,
    current_user: CurrentUserDep,
    service: FellowshipServiceDep,
) -> int:
    return await service.delete_for_user(
        user_id,
        current_user.id,
        fellowship_id,
    )
