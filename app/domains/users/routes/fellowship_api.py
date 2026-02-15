from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.common.exceptions import NotResourceOwnerError
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.exceptions import (
    FellowshipNotFoundError,
    UserNotFoundError,
)
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


class GetUserFellowships(Responses):
    USER_NOT_FOUND = 404, "User with proved ID not found"


@router.get(
    "",
    responses=GetUserFellowships.responses,
    summary="Get user fellowships",
)
async def get_user_fellowships(
    user_id: int,
    service: FellowshipServiceDep,
) -> list[FellowshipViewSchema]:
    try:
        user_fellowships = await service.get_by_user_id(user_id)
        return [FellowshipViewSchema.model_validate(fellowship) for fellowship in user_fellowships]
    except UserNotFoundError:
        raise GetUserFellowships.USER_NOT_FOUND


class GetSingleUserFellowship(GetUserFellowships):
    FELLOWSHIP_NOT_FOUND = 404, "Fellowship with proved ID not found"


@router.get(
    "/{fellowship_id}",
    summary="Get user fellowship by fellowship ID",
)
async def get_single_user_fellowship(
    user_id: int,
    fellowship_id: int,
    service: FellowshipServiceDep,
) -> FellowshipViewSchema:
    try:
        user_fellowship = await service.get_user_fellowship_by_id(
            user_id=user_id,
            fellowship_id=fellowship_id,
        )
        return FellowshipViewSchema.model_validate(user_fellowship)

    except UserNotFoundError:
        raise GetSingleUserFellowship.USER_NOT_FOUND

    except FellowshipNotFoundError:
        raise GetSingleUserFellowship.FELLOWSHIP_NOT_FOUND


class CreateUserFellowshipResponses(GetUserFellowships):
    NOT_RESOURCE_OWNER = 403, "Not resource owner"


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
    try:
        user_fellowship = await service.create_user_fellowship(
            user_id,
            current_user.id,
            **fellowship_creation_data.model_dump(),
        )
        return FellowshipViewSchema.from_orm(user_fellowship)

    except NotResourceOwnerError:
        raise CreateUserFellowshipResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise CreateUserFellowshipResponses.USER_NOT_FOUND


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
    try:
        user_fellowship = await service.update_user_fellowship(
            user_id,
            current_user.id,
            fellowship_id,
            fellowship_update_data.model_dump(),
        )
        return FellowshipViewSchema.from_orm(user_fellowship)

    except NotResourceOwnerError:
        raise UpdateFellowshipResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise UpdateFellowshipResponses.USER_NOT_FOUND


class DeleteFellowshipResponses(
    CreateUserFellowshipResponses,
    GetSingleUserFellowship,
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
    try:
        return await service.delete_user_fellowship(
            user_id,
            current_user.id,
            fellowship_id,
        )

    except NotResourceOwnerError:
        raise DeleteFellowshipResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise DeleteFellowshipResponses.USER_NOT_FOUND

    except FellowshipNotFoundError:
        raise DeleteFellowshipResponses.FELLOWSHIP_NOT_FOUND
