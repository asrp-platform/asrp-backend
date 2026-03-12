from typing import Annotated

from fastapi import Depends

from app.domains.feedback.services import (
    AdditionalDetailService,
    AdditionalDetailServiceDep,
    get_additional_detail_service,
)
from app.domains.memberships.enums import MembershipTypeEnum
from app.domains.memberships.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work
from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import MembershipService, MembershipServiceDep, get_membership_service


class CreateMembershipUseCase:
    def __init__(
        self,
        uow: MembershipUnitOfWork,
        membership_service: MembershipService,
        additional_detail_service: AdditionalDetailService,
        # communication_preference_service: CommunicationPreferenceService
    ) -> None:
        self.uow = uow
        self.membership_service = membership_service
        self.additional_detail_service = additional_detail_service
        # self.communication_preference_service = communication_preference_service

    async def execute(
        self,
        user_id: int,
        is_agrees_communications: bool,
        membership_type: MembershipTypeEnum,
        user_membership_data: dict,
        additional_detail_data: dict,
    ) -> None:
        async with self.uow:
            await self.membership_service.create_membership(
                user_id,
                membership_type,
                **user_membership_data,
            )

            await self.additional_detail_service.create_additional_detail(
                user_id,
                **additional_detail_data
            )

            # await self.communication_preference_service.create_communication_preference(
            #     is_agrees_communications
            # )


def get_create_membership_use_case(
    uow: Annotated[MembershipUnitOfWork, Depends(get_membership_unit_of_work)],
    membership_service: Annotated[MembershipServiceDep, Depends(get_membership_service)],
    additional_detail_service: Annotated[AdditionalDetailServiceDep, Depends(get_additional_detail_service)],
    # communication_preference_service: Annotated[CommunicationPreferenceServiceDep, Depends(get_communication_preference_service)],
) -> CreateMembershipUseCase:
    return CreateMembershipUseCase(uow, membership_service, additional_detail_service)


CreateMembershipUseCaseDep = Annotated[CreateMembershipUseCase, Depends(get_create_membership_use_case)]
