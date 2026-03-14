from typing import Annotated

from fastapi import Depends

from app.domains.feedback.services import (
    FeedbackAdditionalInfoService,
    FeedbackAdditionalInfoServiceDep,
    get_feedback_additional_info_service,
)
from app.domains.memberships.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work
from app.domains.memberships.models import MembershipTypeEnum
from app.domains.memberships.services import MembershipService, MembershipServiceDep, get_membership_service


class CreateMembershipUseCase:
    def __init__(
        self,
        uow: MembershipUnitOfWork,
        membership_service: MembershipService,
        feedback_additional_info_service: FeedbackAdditionalInfoService,
        # communication_preference_service: CommunicationPreferenceService
    ) -> None:
        self.uow = uow
        self.membership_service = membership_service
        self.feedback_additional_info_service = feedback_additional_info_service
        # self.communication_preference_service = communication_preference_service

    async def execute(
        self,
        user_id: int,
        is_agrees_communications: bool,
        membership_type: MembershipTypeEnum,
        user_membership_data: dict,
        feedback_additional_info_data: dict,
    ) -> None:
        async with self.uow:
            await self.membership_service.create_membership(
                user_id,
                membership_type,
                **user_membership_data,
            )

            await self.feedback_additional_info_service.create_feedback_additional_info(
                user_id,
                **feedback_additional_info_data
            )

            # await self.communication_preference_service.create_communication_preference(
            #     is_agrees_communications
            # )


def get_create_membership_use_case(
    uow: Annotated[MembershipUnitOfWork, Depends(get_membership_unit_of_work)],
    membership_service: Annotated[MembershipServiceDep, Depends(get_membership_service)],
    feedback_additional_info_service: Annotated[FeedbackAdditionalInfoServiceDep, Depends(get_feedback_additional_info_service)],
    # communication_preference_service: Annotated[CommunicationPreferenceServiceDep, Depends(get_communication_preference_service)],
) -> CreateMembershipUseCase:
    return CreateMembershipUseCase(uow, membership_service, feedback_additional_info_service)


CreateMembershipUseCaseDep = Annotated[CreateMembershipUseCase, Depends(get_create_membership_use_case)]
