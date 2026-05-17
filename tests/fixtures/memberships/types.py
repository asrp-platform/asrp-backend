import pytest
from faker import Faker

from app.domains.memberships.models import MembershipType, MembershipTypeEnum
from app.domains.shared.transaction_managers import TransactionManager


@pytest.fixture()
def purchasable_membership_type_enum(faker: Faker) -> MembershipTypeEnum:
    return faker.random_element([item for item in MembershipTypeEnum if item != MembershipTypeEnum.HONORARY])


@pytest.fixture()
def purchasable_membership_type_value(purchasable_membership_type_enum: MembershipTypeEnum) -> str:
    return purchasable_membership_type_enum.value


@pytest.fixture()
async def purchasable_membership_type(
    test_transaction_manager: TransactionManager,
    purchasable_membership_type_enum: MembershipTypeEnum,
) -> MembershipType:
    async with test_transaction_manager:
        return await test_transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=purchasable_membership_type_enum,
        )


@pytest.fixture()
async def not_purchasable_membership_type(
    test_transaction_manager: TransactionManager,
) -> MembershipType:
    async with test_transaction_manager:
        return await test_transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=MembershipTypeEnum.HONORARY,
        )


@pytest.fixture()
async def purchasable_membership_type_id(purchasable_membership_type: MembershipType) -> int:
    return purchasable_membership_type.id


@pytest.fixture()
async def not_purchasable_membership_type_id(not_purchasable_membership_type: MembershipType) -> int:
    return not_purchasable_membership_type.id


@pytest.fixture()
def honorary_membership_type_value() -> str:
    return MembershipTypeEnum.HONORARY.value
