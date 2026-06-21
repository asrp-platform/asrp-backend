from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.shared.deps import CurrentUserDep
from app.domains.users.schemas import ProfessionalInformationCreateOrUpdateSchema, ProfessionalInformationViewSchema
from app.domains.users.services import ProfessionalInformationServiceDep


router = APIRouter(tags=["Professional information"], prefix="/users/{user_id}/professional-information")


class GetUserProfessionalInformationResponses(Responses):
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.get(
    "",
    responses=GetUserProfessionalInformationResponses.responses,
    summary="Get user professional information by user ID",
)
async def get_user_professional_information(
    user_id: int,
    professional_information_service: ProfessionalInformationServiceDep,
) -> ProfessionalInformationViewSchema | None:
    return await professional_information_service.get_by_user_id(user_id)


class CreateOrUpdateUserProfessionalInformationResponses(GetUserProfessionalInformationResponses):
    NOT_RESOURCE_OWNER = 403, "Not resource owner"


@router.put(
    "",
    responses=CreateOrUpdateUserProfessionalInformationResponses.responses,
    summary="Create new or update existing user professional information",
)
async def create_or_update_user_professional_information(
    user_id: int,
    current_user: CurrentUserDep,  # noqa: F401, F501
    professional_information_service: ProfessionalInformationServiceDep,
    data: ProfessionalInformationCreateOrUpdateSchema,
) -> ProfessionalInformationViewSchema:
    return await professional_information_service.create_or_update(user_id, current_user.id, **data.model_dump())
