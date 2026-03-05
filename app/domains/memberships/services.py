from typing import Annotated

from fastapi import Depends

from app.domains.memberships.enums import MembershipTypeEnum
from app.domains.memberships.exceptions import MembershipAlreadyExistsError
from app.domains.memberships.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work


class MembershipService:
    def __init__(self, uow: MembershipUnitOfWork):
        self.uow = uow

    async def create_membership(
            self,
            user_id: int,
            membership_type_data: MembershipTypeEnum,
            **kwargs
    ):
        async with self.uow:
            membership = await self.uow.membership_repository.get_first_by_kwargs(user_id=user_id)
            if membership is not None:
                raise MembershipAlreadyExistsError("Membership for provided User already exists")

            membership_type = await self.uow.membership_type_repository.get_first_by_kwargs(type=membership_type_data.value)

            return await self.uow.membership_repository.create(
                user_id=user_id,
                membership_type_id=membership_type.id,
                **kwargs
            )


class MembershipTypeService:
    def __init__(self, uow: MembershipUnitOfWork):
        self.uow = uow


def get_membership_service(
        uow: Annotated[MembershipUnitOfWork,
        Depends(get_membership_unit_of_work)]
)-> MembershipService:
    return MembershipService(uow)


def get_membership_type_service(
        uow: Annotated[MembershipUnitOfWork,
        Depends(get_membership_unit_of_work)]
)-> MembershipTypeService:
    return MembershipTypeService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
MembershipTypeServiceDep = Annotated[MembershipTypeService, Depends(get_membership_type_service)]
