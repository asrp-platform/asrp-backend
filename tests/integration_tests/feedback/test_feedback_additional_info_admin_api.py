from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.domains.feedback.constants import HEAR_ABOUT_ASRP_OPTIONS
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


async def _create_feedback_additional_info(
    test_transaction_manager: TransactionManager,
    user_factory: UserFactory,
    *,
    hear_about_asrp: str,
    tg_username: str | None,
    interest_description: str | None,
    created_at: datetime,
    is_deleted: bool = False,
) -> int:
    user = await user_factory()
    async with test_transaction_manager:
        feedback = await test_transaction_manager.feedback_additional_info_repository.create(
            user_id=user.id,
            hear_about_asrp=hear_about_asrp,
            tg_username=tg_username,
            interest_description=interest_description,
            created_at=created_at,
            _deleted=is_deleted,
        )
    return feedback.id


async def test_get_hear_about_stats_date_range_filter(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager: TransactionManager,
    user_factory: UserFactory,
) -> None:
    dt_2025 = datetime(2025, 3, 10, tzinfo=timezone.utc)
    dt_2024 = datetime(2024, 9, 1, tzinfo=timezone.utc)

    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Telegram or social media",
        tg_username="@tg_1",
        interest_description="I want to contribute to educational events.",
        created_at=dt_2025,
    )
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Telegram or social media",
        tg_username="@tg_2",
        interest_description="Interested in networking.",
        created_at=dt_2025,
    )
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Colleague / word of mouth",
        tg_username=None,
        interest_description=None,
        created_at=dt_2025,
    )
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="USCAP or other conference",
        tg_username=None,
        interest_description="Would like to support community projects.",
        created_at=dt_2025,
    )
    # Legacy non-select value should be folded into "Other" in statistics.
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Legacy source",
        tg_username=None,
        interest_description=None,
        created_at=dt_2025,
    )

    # Out-of-year record should not affect 2025 stats.
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Other",
        tg_username=None,
        interest_description="Out-of-year record",
        created_at=dt_2024,
    )

    response = await client.get(
        "/api/admin/feedback-additional-info/hear-about-stats",
        headers=admin_auth_headers,
        params={"date_from": "2025-01-01", "date_to": "2025-12-31"},
    )

    assert response.status_code == 200

    payload = response.json()
    stats = {item["option"]: item for item in payload["stats"]}

    assert payload["total_responses"] == 5
    assert payload["stats"][0]["option"] == "Telegram or social media"

    for option in HEAR_ABOUT_ASRP_OPTIONS:
        assert option in stats

    assert stats["Telegram or social media"]["count"] == 2
    assert stats["Telegram or social media"]["percentage"] == 40.0
    assert stats["Colleague / word of mouth"]["count"] == 1
    assert stats["Colleague / word of mouth"]["percentage"] == 20.0
    assert stats["USCAP or other conference"]["count"] == 1
    assert stats["USCAP or other conference"]["percentage"] == 20.0
    assert stats["Institutional listserv / email"]["count"] == 0
    assert stats["Institutional listserv / email"]["percentage"] == 0.0
    assert stats["Other"]["count"] == 1
    assert stats["Other"]["percentage"] == 20.0


async def test_get_hear_about_stats_forbidden_without_permission(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/feedback-additional-info/hear-about-stats",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_get_hear_about_stats_filters_by_date_range(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager: TransactionManager,
    user_factory: UserFactory,
) -> None:
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Telegram or social media",
        tg_username=None,
        interest_description="Inside date range",
        created_at=datetime(2025, 6, 7, tzinfo=timezone.utc),
    )
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Colleague / word of mouth",
        tg_username=None,
        interest_description="Outside date range",
        created_at=datetime(2025, 7, 7, tzinfo=timezone.utc),
    )

    response = await client.get(
        "/api/admin/feedback-additional-info/hear-about-stats",
        headers=admin_auth_headers,
        params={"date_from": "2025-06-01", "date_to": "2025-06-30"},
    )

    assert response.status_code == 200
    payload = response.json()
    stats = {item["option"]: item for item in payload["stats"]}

    assert payload["total_responses"] == 1
    assert stats["Telegram or social media"]["count"] == 1
    assert stats["Colleague / word of mouth"]["count"] == 0


async def test_get_hear_about_stats_invalid_date_range(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.get(
        "/api/admin/feedback-additional-info/hear-about-stats",
        headers=admin_auth_headers,
        params={"date_from": "2025-06-11", "date_to": "2025-06-10"},
    )

    assert response.status_code == 422


async def test_get_interests_returns_only_non_null_and_not_deleted(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager: TransactionManager,
    user_factory: UserFactory,
) -> None:
    dt = datetime(2025, 6, 7, tzinfo=timezone.utc)
    token = "interest-filter-token-20250607"

    included_id_1 = await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Other",
        tg_username="@tg_public",
        interest_description=f"Interested in committee work and mentorship. {token}",
        created_at=dt,
    )
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Other",
        tg_username="@tg_hidden",
        interest_description=None,
        created_at=dt,
    )
    included_id_2 = await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Other",
        tg_username=None,
        interest_description=f"Interested in speaker opportunities. {token}",
        created_at=dt,
    )
    await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Other",
        tg_username="@deleted",
        interest_description="Should not be shown",
        created_at=dt,
        is_deleted=True,
    )

    response = await client.get(
        "/api/admin/feedback-additional-info/interests",
        headers=admin_auth_headers,
        params={"page": 1, "page_size": 50, "search": token},
    )

    assert response.status_code == 200

    payload = response.json()
    ids = {item["id"] for item in payload["data"]}

    assert payload["count"] == 2
    assert included_id_1 in ids
    assert included_id_2 in ids

    for item in payload["data"]:
        assert item["interest_description"] is not None


async def test_get_interests_not_authorized(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/admin/feedback-additional-info/interests")

    assert response.status_code == 401


async def test_get_interests_by_user_forbidden(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/feedback-additional-info/interests",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_get_interests_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/feedback-additional-info/interests",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_get_interests_filters_by_date_range(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager: TransactionManager,
    user_factory: UserFactory,
) -> None:
    token = "interest-date-range-token"
    dt_inside = datetime(2025, 6, 7, tzinfo=timezone.utc)
    dt_outside = datetime(2025, 6, 20, tzinfo=timezone.utc)

    included_id = await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Other",
        tg_username="@inside",
        interest_description=f"Included by date range {token}",
        created_at=dt_inside,
    )
    excluded_id = await _create_feedback_additional_info(
        test_transaction_manager,
        user_factory,
        hear_about_asrp="Other",
        tg_username="@outside",
        interest_description=f"Excluded by date range {token}",
        created_at=dt_outside,
    )

    response = await client.get(
        "/api/admin/feedback-additional-info/interests",
        headers=admin_auth_headers,
        params={
            "page": 1,
            "page_size": 50,
            "search": token,
            "date_from": "2025-06-01",
            "date_to": "2025-06-10",
        },
    )

    assert response.status_code == 200

    payload = response.json()
    ids = {item["id"] for item in payload["data"]}

    assert payload["count"] == 1
    assert included_id in ids
    assert excluded_id not in ids


async def test_get_interests_invalid_date_range(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.get(
        "/api/admin/feedback-additional-info/interests",
        headers=admin_auth_headers,
        params={
            "page": 1,
            "page_size": 10,
            "date_from": "2025-06-11",
            "date_to": "2025-06-10",
        },
    )

    assert response.status_code == 422
