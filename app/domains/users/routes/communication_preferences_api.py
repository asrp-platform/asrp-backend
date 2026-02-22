from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.common.exceptions import NotResourceOwnerError
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.exceptions import InvalidCommunicationFieldError, UserNotFoundError
from app.domains.users.schemas import CommunicationPreferenceUpdateSchema, CommunicationPreferenceViewSchema
from app.domains.users.services import CommunicationPreferenceServiceDep

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
    communication_preferences_service: CommunicationPreferenceServiceDep,
) -> CommunicationPreferenceViewSchema:
    try:
        preferences = await communication_preferences_service.get_preferences(
            user_id=user_id,
            current_user_id=current_user.id
        )
        return CommunicationPreferenceViewSchema.model_validate(preferences)
    except UserNotFoundError:
        raise GetCommunicationPreferencesResponses.USER_NOT_FOUND
    except NotResourceOwnerError:
        raise GetCommunicationPreferencesResponses.NOT_RESOURCE_OWNER


class UpdateCommunicationPreferenceResponses(GetCommunicationPreferencesResponses):
    INVALID_FIELD = 400, "Invalid communication field or trying to modify required preference"
    MEMBERSHIP_NOT_DISABLE = 400, "Membership & account notifications are required and cannot be disabled"


@router.patch(
    "",
    responses=UpdateCommunicationPreferenceResponses.responses,
    summary="Update a single communication preference",
)
async def update_communication_preference(
    user_id: int,
    current_user: CurrentUserDep,  # noqa: Auth dependency
    communication_preferences_service: CommunicationPreferenceServiceDep,
    preference_update: CommunicationPreferenceUpdateSchema,
) -> CommunicationPreferenceViewSchema:
    try:
        updated_preferences = await communication_preferences_service.update_preference(
            user_id=user_id,
            current_user_id=current_user.id,
            field=preference_update.field,
            value=preference_update.value
        )
        return CommunicationPreferenceViewSchema.model_validate(updated_preferences)
    except UserNotFoundError:
        raise UpdateCommunicationPreferenceResponses.USER_NOT_FOUND
    except NotResourceOwnerError:
        raise UpdateCommunicationPreferenceResponses.NOT_RESOURCE_OWNER
    except InvalidCommunicationFieldError as e:
        if "Membership & account notifications" in str(e):
            raise UpdateCommunicationPreferenceResponses.MEMBERSHIP_NOT_DISABLE
        raise UpdateCommunicationPreferenceResponses.INVALID_FIELD
