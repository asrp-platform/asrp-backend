from unittest.mock import AsyncMock

import pytest
from starlette.exceptions import HTTPException

from app.domains.memberships.exceptions import (
    CantChangeToHonoraryMembershipError,
    CheckoutSessionCreationError,
    InvalidMembershipTypeUpgradeError,
    SameMembershipTypeChangeRequestError,
)
from app.domains.memberships.schemas.membership_requests import UpgradeMembershipSchema
from app.domains.users.routes.current_user_api.current_user_membership_api import (
    create_membership_upgrade_checkout,
)


pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("domain_error", "expected_status", "expected_detail"),
    [
        (SameMembershipTypeChangeRequestError(), 422, "Can't change membership type for the same type"),
        (CantChangeToHonoraryMembershipError(), 422, "Can't change membership type to HONORARY"),
        (InvalidMembershipTypeUpgradeError(), 422, "Invalid membership type upgrade"),
        (CheckoutSessionCreationError(), 502, "Failed to create checkout session"),
    ],
)
async def test_upgrade_membership_maps_domain_errors_to_http(
    domain_error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    use_case = AsyncMock()
    use_case.execute.side_effect = domain_error

    with pytest.raises(HTTPException) as exc_info:
        await create_membership_upgrade_checkout(
            current_user=object(),
            current_user_membership=object(),
            use_case=use_case,
            body=UpgradeMembershipSchema(target_membership_type_id=2),
        )

    assert exc_info.value.status_code == expected_status
    assert exc_info.value.detail == expected_detail


async def test_upgrade_membership_returns_checkout_url() -> None:
    use_case = AsyncMock()
    use_case.execute.return_value = "https://checkout.example/session"

    response = await create_membership_upgrade_checkout(
        current_user=object(),
        current_user_membership=object(),
        use_case=use_case,
        body=UpgradeMembershipSchema(target_membership_type_id=2),
    )

    assert response.checkout_session_url == "https://checkout.example/session"
