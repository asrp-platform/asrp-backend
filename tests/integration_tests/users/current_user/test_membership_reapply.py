from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

import app.domains.memberships.use_cases.membership_requests.reapply_membership_application as reapply_module
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


@pytest.fixture()
def reapply_checkout_session_mock(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    checkout_session = SimpleNamespace(
        id="cs_reapply_test",
        status="open",
        payment_status="unpaid",
        url="https://checkout.stripe.com/reapply-test",
    )

    async def create_checkout_session(*, membership_request, membership_type, payment):
        return SimpleNamespace(
            session=checkout_session,
            provider_data={
                "membership_request_id": membership_request.id,
                "payment_id": str(payment.id),
                "checkout_session_id": checkout_session.id,
                "checkout_session_status": checkout_session.status,
                "payment_intent_status": checkout_session.payment_status,
                "url": checkout_session.url,
            },
        )

    mock = AsyncMock(side_effect=create_checkout_session)
    monkeypatch.setattr(reapply_module, "create_membership_application_checkout_session", mock)
    return mock


async def test_membership_reapply(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    rejected_membership_request: MembershipRequest,
    auth_headers: AuthHeaders,
    membership_reapply_payload: dict,
    reapply_checkout_session_mock: AsyncMock,
):
    response = await client.post(
        "/api/users/current-user/membership-requests/reapplies",
        headers=auth_headers,
        json=membership_reapply_payload,
    )
    async with test_transaction_manager:
        updated_membership_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=rejected_membership_request.id
        )
    assert response.status_code == 201
    assert updated_membership_request.status == MembershipRequestStatusEnum.PAYMENT_PENDING
    assert updated_membership_request.membership_type_id == membership_reapply_payload["membership_type_id"]
    assert "checkout_session_url" in response.json()
    assert reapply_checkout_session_mock.await_count == 1


async def test_membership_reapply_honorary(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    rejected_membership_request: MembershipRequest,
    auth_headers: AuthHeaders,
    membership_reapply_payload: dict,
    not_purchasable_membership_type_id,
    reapply_checkout_session_mock: AsyncMock,
):
    membership_reapply_payload_honorary = membership_reapply_payload.copy()
    membership_reapply_payload_honorary["membership_type_id"] = not_purchasable_membership_type_id

    response = await client.post(
        "/api/users/current-user/membership-requests/reapplies",
        headers=auth_headers,
        json=membership_reapply_payload_honorary,
    )

    async with test_transaction_manager:
        updated_membership_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=rejected_membership_request.id
        )
    assert response.status_code == 422
    assert updated_membership_request.status == MembershipRequestStatusEnum.REJECTED
    assert updated_membership_request.membership_type_id == membership_reapply_payload["membership_type_id"]
    reapply_checkout_session_mock.assert_not_awaited()


async def test_membership_reapply_already_paid(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    rejected_membership_request: MembershipRequest,
    auth_headers: AuthHeaders,
    membership_reapply_payload: dict,
    test_user: User,
    reapply_checkout_session_mock: AsyncMock,
):
    async with test_transaction_manager:
        await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=Decimal("120.00"),
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            provider_data={"payment_intent_id": "pi_reapply_already_paid"},
            user_id=test_user.id,
            membership_request_id=rejected_membership_request.id,
        )

    response = await client.post(
        "/api/users/current-user/membership-requests/reapplies",
        headers=auth_headers,
        json=membership_reapply_payload,
    )

    async with test_transaction_manager:
        updated_membership_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=rejected_membership_request.id
        )

    assert response.status_code == 409
    assert updated_membership_request.status == MembershipRequestStatusEnum.REJECTED
    assert updated_membership_request.membership_type_id == membership_reapply_payload["membership_type_id"]
    reapply_checkout_session_mock.assert_not_awaited()


async def test_membership_reapply_request_not_rejected(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    user_membership_request: MembershipRequest,
    auth_headers: AuthHeaders,
    membership_reapply_payload: dict,
    reapply_checkout_session_mock: AsyncMock,
):
    response = await client.post(
        "/api/users/current-user/membership-requests/reapplies",
        headers=auth_headers,
        json=membership_reapply_payload,
    )

    async with test_transaction_manager:
        updated_membership_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=user_membership_request.id
        )

    assert response.status_code == 409
    assert updated_membership_request.status == MembershipRequestStatusEnum.PAYMENT_PENDING
    assert updated_membership_request.membership_type_id == user_membership_request.membership_type_id
    reapply_checkout_session_mock.assert_not_awaited()
