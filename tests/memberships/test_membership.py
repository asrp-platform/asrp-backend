import pytest
from httpx import AsyncClient

from app.domains.memberships.infrastructure import MembershipsTransactionManagerBase
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.users.infrastructure import UserTransactionManagerBase
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_create_user_membership(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_data: dict,
    user_uow: UserTransactionManagerBase,
    membership_uow: MembershipsTransactionManagerBase,
) -> None:
    response = await client.post(
        "api/users/current-user/membership-requests", headers=auth_headers, json=user_membership_data
    )

    async with membership_uow:
        user_membership = await membership_uow.membership_request_repository.get_first_by_kwargs(user_id=test_user.id)
        communication_preferences = await user_uow.communication_preferences_repository.get_first_by_kwargs(
            user_id=test_user.id
        )

    assert not communication_preferences.newsletters
    assert not communication_preferences.events_meetings
    assert not communication_preferences.committees_leadership
    assert not communication_preferences.volunteer_opportunities

    assert user_membership.status == MembershipRequestStatusEnum.PAYMENT_PENDING
    assert response.status_code == 201


async def test_create_user_membership_is_agrees_communications_true(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_data: dict,
    user_uow: UserTransactionManagerBase,
) -> None:
    user_membership_data["is_agrees_communications"] = True

    response = await client.post(
        "api/users/current-user/membership-requests", headers=auth_headers, json=user_membership_data
    )

    async with user_uow:
        communication_preferences = await user_uow.communication_preferences_repository.get_first_by_kwargs(
            user_id=test_user.id
        )

    assert communication_preferences.newsletters
    assert communication_preferences.events_meetings
    assert communication_preferences.committees_leadership
    assert communication_preferences.volunteer_opportunities

    assert response.status_code == 201


async def test_create_user_membership_not_authenticated(client: AsyncClient, user_membership_data: dict) -> None:
    response = await client.post("api/users/current-user/membership-requests", json=user_membership_data)

    assert response.status_code == 401


async def test_create_user_membership_already_exists(
    client: AsyncClient, user_membership: MembershipRequest, auth_headers: AuthHeaders, user_membership_data: dict
) -> None:
    response = await client.post(
        "api/users/current-user/membership-requests", headers=auth_headers, json=user_membership_data
    )

    assert response.status_code == 409
