import pytest
from httpx import AsyncClient

from app.domains.memberships.infrastructure import MembershipUnitOfWork
from app.domains.memberships.models import ApprovalStatusEnum, UserMembership
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_create_membership(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    membership_data: dict,
    membership_uow: MembershipUnitOfWork
) -> None:
    response = await client.post(
        "api/memberships",
        headers=auth_headers,
        json=membership_data
    )

    async with membership_uow:
        membership = await membership_uow.membership_repository.get_first_by_kwargs(user_id=test_user.id)

    assert membership.approval_status == ApprovalStatusEnum.PENDING
    assert response.status_code == 201


async def test_create_membership_not_authenticated(
    client: AsyncClient,
    membership_data: dict
) -> None:
    response = await client.post(
        "api/memberships",
        json=membership_data
    )

    assert response.status_code == 401


async def test_create_membership_already_exists(
    client: AsyncClient,
    membership: UserMembership,
    auth_headers: AuthHeaders,
    membership_data: dict
) -> None:
    response = await client.post(
        "api/memberships",
        headers=auth_headers,
        json=membership_data
    )

    assert response.status_code == 409
