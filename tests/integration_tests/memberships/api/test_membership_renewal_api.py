from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.domains.memberships.models import UserMembership
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.use_cases.current_user_membership import renew_membership as renew_membership_module
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


@pytest.fixture()
def mock_renewal_checkout(monkeypatch):
    async def _create_checkout_session(*, payment, membership_type, user_membership, user_email):
        session = SimpleNamespace(
            id="cs_test_membership_renewal",
            status="open",
            payment_status="unpaid",
            url="https://checkout.stripe.com/test/membership-renewal",
        )
        return SimpleNamespace(
            session=session,
            provider_data={
                "user_membership_id": user_membership.id,
                "payment_id": str(payment.id),
                "checkout_session_id": session.id,
                "checkout_session_status": session.status,
                "payment_intent_status": session.payment_status,
                "url": session.url,
            },
        )

    monkeypatch.setattr(
        renew_membership_module,
        "create_membership_renewal_checkout_session",
        _create_checkout_session,
    )


async def test_renew_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    user_membership: UserMembership,
    mock_renewal_checkout,
) -> None:
    response = await client.post(
        "/api/users/current-user/membership/renewal",
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json() == {
        "checkout_session_url": "https://checkout.stripe.com/test/membership-renewal",
    }


async def test_renew_membership_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/users/current-user/membership/renewal",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


async def test_renew_membership_no_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.post(
        "/api/users/current-user/membership/renewal",
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "No active membership"


async def test_renew_terminated_membership(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    auth_headers: AuthHeaders,
    user_membership: UserMembership,
) -> None:
    async with test_transaction_manager:
        await test_transaction_manager.user_membership_repository.update(
            user_membership.id,
            terminated=True,
            termination_reason="Test termination",
            terminated_at=datetime.now(timezone.utc),
        )

    response = await client.post(
        "/api/users/current-user/membership/renewal",
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Membership is permanently blocked"


async def test_renew_suspended_membership(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    auth_headers: AuthHeaders,
    user_membership: UserMembership,
) -> None:
    async with test_transaction_manager:
        suspended_until = datetime.now(timezone.utc) + timedelta(days=1)
        await test_transaction_manager.user_membership_repository.update(
            user_membership.id,
            suspended_until=suspended_until,
            suspension_reason="Test suspension",
            suspended_at=datetime.now(timezone.utc),
        )

    response = await client.post(
        "/api/users/current-user/membership/renewal",
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Membership is temporarily blocked until 2026-06-08T12:00:00+00:00"


async def test_renew_membership_checkout_creation_failed(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    user_membership: UserMembership,
    monkeypatch,
) -> None:
    async def _raise_checkout_error(*, payment, membership_type, user_membership, user_email):
        raise RuntimeError("Stripe is unavailable")

    monkeypatch.setattr(
        renew_membership_module,
        "create_membership_renewal_checkout_session",
        _raise_checkout_error,
    )

    response = await client.post(
        "/api/users/current-user/membership/renewal",
        headers=auth_headers,
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to create checkout session"
