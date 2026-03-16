from fastapi import APIRouter
from fastapi_exception_responses import Responses
from pydantic import ValidationError

from app.core.common.exceptions import NotResourceOwnerError
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.exceptions import UserNotFoundError
from app.domains.users.schemas import CommunicationPreferencesUpdateSchema, CommunicationPreferencesViewSchema
from app.domains.users.services import CommunicationPreferencesServiceDep

router = APIRouter(tags=["Communication Preferences"], prefix="/users/{user_id}/communication-preferences")


class GetCommunicationPreferencesResponses(Responses):
    USER_NOT_FOUND = 404, "User with provided ID not found"
    NOT_RESOURCE_OWNER = 403, "Not resource owner"


@router.get(
    "",
    responses=GetCommunicationPreferencesResponses.responses,
    summary="Get user communication preferences by user ID",
)
async def get_user_communication_preferences(
    user_id: int,
    current_user: CurrentUserDep,  # noqa: Auth dependency
    communication_preferences_service: CommunicationPreferencesServiceDep,
) -> CommunicationPreferencesViewSchema:
    try:
        communication_preferences = await communication_preferences_service.get_preferences(
            user_id=user_id,
            current_user_id=current_user.id
        )
        return CommunicationPreferencesViewSchema.model_validate(communication_preferences)
    except UserNotFoundError:
        raise GetCommunicationPreferencesResponses.USER_NOT_FOUND
    except NotResourceOwnerError:
        raise GetCommunicationPreferencesResponses.NOT_RESOURCE_OWNER


class UpdateCommunicationPreferencesResponses(GetCommunicationPreferencesResponses):
    INVALID_FIELD = 400, "Invalid communication field or trying to modify required preference"
    MEMBERSHIP_NOT_DISABLE = 400, "Membership & account notifications are required and cannot be disabled"
    VALIDATION_ERROR = 422, "Validation error in request data"

@router.patch(
    "",
    responses=UpdateCommunicationPreferencesResponses.responses,
    summary="Update a single communication preference",
)
async def update_communication_preferences(
    user_id: int,
    current_user: CurrentUserDep,  # noqa: Auth dependency
    communication_preferences_service: CommunicationPreferencesServiceDep,
    preference_update: CommunicationPreferencesUpdateSchema,
) -> CommunicationPreferencesViewSchema:
    try:
        updated_preference = await communication_preferences_service.update_preference(
            user_id=user_id,
            current_user_id=current_user.id,
            update_data=preference_update
        )
        return CommunicationPreferencesViewSchema.model_validate(updated_preference)
    except UserNotFoundError:
        raise UpdateCommunicationPreferencesResponses.USER_NOT_FOUND
    except NotResourceOwnerError:
        raise UpdateCommunicationPreferencesResponses.NOT_RESOURCE_OWNER
    except ValidationError as e:
        errors = e.errors()
        for error in errors:
            if error.get('loc') == ('membership_account_notifications',):
                raise UpdateCommunicationPreferencesResponses.MEMBERSHIP_NOT_DISABLE
        raise UpdateCommunicationPreferencesResponses.VALIDATION_ERROR
