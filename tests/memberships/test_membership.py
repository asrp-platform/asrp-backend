import pytest
from httpx import AsyncClient

from app.domains.memberships.infrastructure import MembershipsUnitOfWork
from app.domains.memberships.models import ApprovalStatusEnum, UserMembership
from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_create_user_membership(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_data: dict,
    user_uow: UserUnitOfWork,
    membership_uow: MembershipsUnitOfWork
) -> None:
    response = await client.post(
        "api/current-user/membership",
        headers=auth_headers,
        json=user_membership_data
    )

    async with membership_uow:
        user_membership = await membership_uow.user_membership_repository.get_first_by_kwargs(user_id=test_user.id)
        communication_preferences = await user_uow.communication_preferences_repository.get_first_by_kwargs(
            user_id=test_user.id
        )

    assert communication_preferences.newsletters == False
    assert communication_preferences.events_meetings == False
    assert communication_preferences.committees_leadership == False
    assert communication_preferences.volunteer_opportunities == False

    assert user_membership.approval_status == ApprovalStatusEnum.PENDING
    assert response.status_code == 201


async def test_create_user_membership_is_agrees_communications_true(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_data: dict,
    user_uow: UserUnitOfWork
) -> None:
    user_membership_data["is_agrees_communications"] = True

    response = await client.post(
        "api/current-user/membership",
        headers=auth_headers,
        json=user_membership_data
    )

    async with user_uow:
        communication_preferences = await user_uow.communication_preferences_repository.get_first_by_kwargs(
            user_id=test_user.id
        )

    assert communication_preferences.newsletters == True
    assert communication_preferences.events_meetings == True
    assert communication_preferences.committees_leadership == True
    assert communication_preferences.volunteer_opportunities == True


async def test_create_user_membership_not_authenticated(
    client: AsyncClient,
    user_membership_data: dict
) -> None:
    response = await client.post(
        "api/current-user/membership",
        json=user_membership_data
    )

    assert response.status_code == 401


async def test_create_user_membership_already_exists(
    client: AsyncClient,
    user_membership: UserMembership,
    auth_headers: AuthHeaders,
    user_membership_data: dict
) -> None:
    response = await client.post(
        "api/current-user/membership",
        headers=auth_headers,
        json=user_membership_data
    )

    assert response.status_code == 409
