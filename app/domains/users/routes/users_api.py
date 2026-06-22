from typing import Annotated

from fastapi import APIRouter, Path
from fastapi_exception_responses import Responses

from app.domains.shared.deps import CurrentUserDep
from app.domains.users.schemas import (
    CommunicationPreferencesUpdateSchema,
    CommunicationPreferencesViewSchema,
    UserSchema,
)
from app.domains.users.services import UserServiceDep
from app.domains.users.use_cases.retrieve_user_communication_preferences import (
    RetrieveCommunicationPreferencesUseCaseDep,
)
from app.domains.users.use_cases.update_user_communication_preferences import UpdateCommunicationPreferencesUseCaseDep


router = APIRouter(tags=["Users"], prefix="/users")


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
    return await use_case.execute(user_id)


@router.patch("/{user_id}/communication-preferences")
async def update_user_communication_preferences(
    user_id: Annotated[int, Path()],
    current_user: CurrentUserDep,
    use_case: UpdateCommunicationPreferencesUseCaseDep,
    update_data: CommunicationPreferencesUpdateSchema,
) -> CommunicationPreferencesViewSchema:
    return await use_case.execute(user_id, current_user.id, update_data.model_dump(exclude_none=True))
