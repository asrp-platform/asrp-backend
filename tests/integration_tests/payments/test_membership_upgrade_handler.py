from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.memberships.models import MembershipTypeEnum
from app.domains.payments.purpose_handlers.membership_upgrade import MembershipUpgradeHandler


pytestmark = pytest.mark.anyio


async def test_checkout_session_completed_upgrades_membership() -> None:
    user_membership_service = AsyncMock()
    membership_type_service = AsyncMock()
    payment_service = AsyncMock()
    handler = MembershipUpgradeHandler(
        user_membership_service=user_membership_service,
        membership_type_service=membership_type_service,
        payment_service=payment_service,
    )
    user_membership = SimpleNamespace(id=10, membership_type_id=1)
    target_membership_type = SimpleNamespace(id=2, type=MembershipTypeEnum.ACTIVE)
    user_membership_service.get_user_membership_by_id.return_value = user_membership
    membership_type_service.get_membership_type_by_id.return_value = target_membership_type
    payment = SimpleNamespace(id="payment-id", provider_data={"user_membership_id": 10})
    session = SimpleNamespace(
        id="checkout-id",
        status="complete",
        payment_status="paid",
        metadata={"target_membership_type_id": "2"},
    )
    event = SimpleNamespace(id="event-id", data=SimpleNamespace(object=session))

    await handler.on_checkout_session_completed(payment, event)

    user_membership_service.update_user_membership.assert_awaited_once_with(10, membership_type_id=2)
    membership_type_service.get_membership_type_by_id.assert_awaited_once_with(membership_type_id=2)
    payment_service.update_payment.assert_awaited_once()
    provider_data = payment_service.update_payment.await_args.kwargs["provider_data"]
    assert provider_data["previous_membership_type_id"] == 1
    assert provider_data["target_membership_type_id"] == 2
    assert provider_data["checkout_session_id"] == "checkout-id"


async def test_checkout_session_completed_ignores_unpaid_session() -> None:
    user_membership_service = AsyncMock()
    membership_type_service = AsyncMock()
    payment_service = AsyncMock()
    handler = MembershipUpgradeHandler(
        user_membership_service=user_membership_service,
        membership_type_service=membership_type_service,
        payment_service=payment_service,
    )
    payment = SimpleNamespace(id="payment-id", provider_data={})
    session = SimpleNamespace(id="checkout-id", payment_status="unpaid", metadata={})
    event = SimpleNamespace(id="event-id", data=SimpleNamespace(object=session))

    await handler.on_checkout_session_completed(payment, event)

    user_membership_service.get_user_membership_by_id.assert_not_awaited()
    user_membership_service.update_user_membership.assert_not_awaited()
    payment_service.update_payment.assert_not_awaited()
