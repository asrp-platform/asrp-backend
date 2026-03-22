from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.filters import UsersFilter
from app.domains.users.schemas import (
    CommunicationPreferencesUpdateSchema,
    CommunicationPreferencesViewSchema,
    UserSchema,
)
from app.domains.users.services import NameChangeRequestServiceDep, UserServiceDep
from app.domains.users.use_cases.retrieve_user_communication_preferences import (
    RetrieveCommunicationPreferencesRequest,
    RetrieveCommunicationPreferencesUseCaseDep,
)
from app.domains.users.use_cases.update_user_communication_preferences import (
    UpdateCommunicationPreferencesRequest,
    UpdateCommunicationPreferencesUseCaseDep,
)
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Users"], prefix="/users")


class UserListResponses(InvalidRequestParamsResponses):
    pass


@router.get("")
async def get_users(
    current_user: CurrentUserDep,  # noqa
    user_service: UserServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[UsersFilter, Depends()] = None,
) -> PaginatedResponse[UserSchema]:
    try:
        users, users_count = await user_service.get_all_paginated_counted(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [UserSchema.from_orm(user) for user in users]
        return PaginatedResponse(
            count=users_count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise UserListResponses.INVALID_SORTER_FIELD


class GetUserResponses(Responses):
    USER_NOT_FOUND = 404, "User with the provided email was not found"


@router.get("/{user_id}", summary="Get user by id", responses=GetUserResponses.responses)
async def get_user(
    user_id: Annotated[int, Path(...)],
    current_user: CurrentUserDep,  # noqa
    user_service: UserServiceDep,
) -> UserSchema:
    user = await user_service.get_user_by_kwargs(id=user_id)
    if user is None:
        raise GetUserResponses.USER_NOT_FOUND
    return UserSchema.from_orm(user)


@router.get("/{user_id}/communication-preferences")
async def get_user_communication_preferences(
    user_id: Annotated[int, Path()],
    current_user: CurrentUserDep,  # noqa
    use_case: RetrieveCommunicationPreferencesUseCaseDep,
) -> CommunicationPreferencesViewSchema:
    request = RetrieveCommunicationPreferencesRequest(user_id=user_id)
    preferences = await use_case.execute(request)
    return CommunicationPreferencesViewSchema.model_validate(preferences)


@router.patch("/{user_id}/communication-preferences")
async def update_user_communication_preferences(
    user_id: Annotated[int, Path()],
    current_user: CurrentUserDep,
    use_case: UpdateCommunicationPreferencesUseCaseDep,
    update_data: CommunicationPreferencesUpdateSchema,
):
    request = UpdateCommunicationPreferencesRequest(
        user_id=user_id,
        current_user_id=current_user.id,
        update_data=update_data.model_dump(exclude_none=True),
    )

    updated_preferences = await use_case.execute(request)
    return CommunicationPreferencesViewSchema.model_validate(updated_preferences)