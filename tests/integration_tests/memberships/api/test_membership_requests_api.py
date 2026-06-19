from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.payments.models import PaymentPurposeEnum, PaymentStatusEnum
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


def make_checkout_session(url: str = "https://checkout.stripe.com/test-session") -> SimpleNamespace:
    return SimpleNamespace(
        id="cs_membership_request",
        status="open",
        payment_status="unpaid",
        url=url,
    )


async def test_create_user_membership(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_request_data,
    test_transaction_manager: TransactionManager,
) -> None:
    with patch(
        "app.domains.payments.stripe.utils.create_checkout_session",
        new=AsyncMock(return_value=make_checkout_session()),
    ):
        response = await client.post(
            "api/users/current-user/membership-requests",
            headers=auth_headers,
            json=user_membership_request_data,
        )

    async with test_transaction_manager:
        user_membership = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            user_id=test_user.id
        )
        communication_preferences = (
            await test_transaction_manager.communication_preferences_repository.get_first_by_kwargs(
                user_id=test_user.id
            )
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
    user_membership_request_data,
    test_transaction_manager: TransactionManager,
) -> None:
    user_membership_request_data["is_agrees_communications"] = True

    with patch(
        "app.domains.payments.stripe.utils.create_checkout_session",
        new=AsyncMock(return_value=make_checkout_session()),
    ):
        response = await client.post(
            "api/users/current-user/membership-requests",
            headers=auth_headers,
            json=user_membership_request_data,
        )

    async with test_transaction_manager:
        communication_preferences = (
            await test_transaction_manager.communication_preferences_repository.get_first_by_kwargs(
                user_id=test_user.id
            )
        )

    assert communication_preferences.newsletters
    assert communication_preferences.events_meetings
    assert communication_preferences.committees_leadership
    assert communication_preferences.volunteer_opportunities

    assert response.status_code == 201


async def test_create_user_membership_not_authenticated(client: AsyncClient, user_membership_request_data) -> None:
    response = await client.post("api/users/current-user/membership-requests", json=user_membership_request_data)

    assert response.status_code == 401


async def test_create_user_membership_already_exists(
    client: AsyncClient, user_membership_request, auth_headers: AuthHeaders, user_membership_request_data
) -> None:
    response = await client.post(
        "api/users/current-user/membership-requests", headers=auth_headers, json=user_membership_request_data
    )

    assert response.status_code == 409, response.json()


async def test_create_user_membership_honorary_not_allowed(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    honorary_user_membership_request_data,
) -> None:
    response = await client.post(
        "api/users/current-user/membership-requests",
        headers=auth_headers,
        json=honorary_user_membership_request_data,
    )

    assert response.status_code == 422


async def test_create_user_membership_checkout_failure_returns_bad_gateway(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_request_data,
    test_transaction_manager: TransactionManager,
) -> None:
    with patch(
        "app.domains.payments.stripe.utils.create_checkout_session",
        new=AsyncMock(side_effect=RuntimeError("stripe is down")),
    ):
        response = await client.post(
            "api/users/current-user/membership-requests",
            headers=auth_headers,
            json=user_membership_request_data,
        )

    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(
            user_id=test_user.id,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
        )

    assert response.status_code == 502
    assert payment.status == PaymentStatusEnum.FAILED
    assert payment.provider_data["error_type"] == "checkout_session_error"


async def test_create_new_payment_attempt(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_request,
    test_transaction_manager: TransactionManager,
) -> None:
    checkout_session = make_checkout_session("https://checkout.stripe.com/payment-attempt")

    with patch(
        "app.domains.payments.stripe.utils.create_checkout_session",
        new=AsyncMock(return_value=checkout_session),
    ):
        response = await client.post("api/users/current-user/membership-requests/payments", headers=auth_headers)

    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(
            user_id=test_user.id,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
        )

    assert response.status_code == 201
    assert response.json()["checkout_session_url"] == checkout_session.url
    assert payment.status == PaymentStatusEnum.PENDING
    assert payment.provider_data["checkout_session_id"] == checkout_session.id


async def test_create_new_payment_attempt_checkout_failure_returns_bad_gateway(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    user_membership_request,
    test_transaction_manager: TransactionManager,
) -> None:
    with patch(
        "app.domains.payments.stripe.utils.create_checkout_session",
        new=AsyncMock(side_effect=RuntimeError("stripe is down")),
    ):
        response = await client.post("api/users/current-user/membership-requests/payments", headers=auth_headers)

    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(
            user_id=test_user.id,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
        )

    assert response.status_code == 502
    assert payment.status == PaymentStatusEnum.FAILED
    assert payment.provider_data["error_type"] == "checkout_session_error"
