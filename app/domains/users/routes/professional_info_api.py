from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.common.exceptions import NotFoundError
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.schemas import ProfessionalInformationCreateOrUpdateSchema, ProfessionalInformationViewSchema
from app.domains.users.services import ProfessionalInformationServiceDep

router = APIRouter(tags=["Professional information"], prefix="/users/{user_id}/professional-information")


class GetUserProfessionalInformationResponses(Responses):
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.get(
    "/",
    responses=GetUserProfessionalInformationResponses.responses,
    summary="Get user professional information by user ID",
)
async def get_user_professional_information(
    user_id: int,
    professional_information_service: ProfessionalInformationServiceDep,
) -> ProfessionalInformationViewSchema:
    try:
        user_professional_information = await professional_information_service.get_by_user_id(user_id)
        return ProfessionalInformationViewSchema.from_orm(user_professional_information)
    except NotFoundError:
        raise GetUserProfessionalInformationResponses.USER_NOT_FOUND


class CreateOrUpdateUserProfessionalInformationResponses(GetUserProfessionalInformationResponses):
    pass


@router.put(
    "/",
    responses=CreateOrUpdateUserProfessionalInformationResponses.responses,
    summary="Create new or update existing user professional information",
)
async def create_or_update_user_professional_information(
    user_id: int,
    current_user: CurrentUserDep,  # noqa: Auth dependency
    professional_information_service: ProfessionalInformationServiceDep,
    data: ProfessionalInformationCreateOrUpdateSchema,
) -> ProfessionalInformationViewSchema:
    try:
        updated_user_professional_information = await professional_information_service.create_or_update(
            user_id, **data.model_dump()
        )
        return ProfessionalInformationViewSchema.from_orm(updated_user_professional_information)
    except NotFoundError:
        raise CreateOrUpdateUserProfessionalInformationResponses.USER_NOT_FOUND
