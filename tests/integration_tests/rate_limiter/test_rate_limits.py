import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from app.core.config import TierLimit, settings
from app.domains.memberships.models import MembershipRequest
from app.domains.memberships.services import UserMembershipService
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


async def test_guest_rate_limit_exceeds_capacity(
    client: AsyncClient,
    redis_client: Redis,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_GUEST_LIMITS",
        TierLimit(capacity=2, refill_rate=0.0),
    )

    response = await client.get("/healthcheck")
    assert response.status_code == 200

    response = await client.get("/healthcheck")
    assert response.status_code == 200

    response = await client.get("/healthcheck")
    assert response.status_code == 429


async def test_authenticated_rate_limit_exceeds_capacity(
    client: AsyncClient,
    redis_client: Redis,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_AUTHENTICATED_LIMITS",
        TierLimit(capacity=2, refill_rate=0.0),
    )

    response = await client.get("/healthcheck", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/healthcheck", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/healthcheck", headers=auth_headers)
    assert response.status_code == 429


async def test_paid_member_rate_limit_exceeds_capacity(
    client: AsyncClient,
    redis_client: Redis,
    admin_user: User,
    test_user: User,
    user_membership_service: UserMembershipService,
    paid_membership_request: MembershipRequest,
    auth_headers,
    monkeypatch,
):
    await user_membership_service.create_user_membership(
        user_id=test_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        membership_request_id=paid_membership_request.id,
        membership_type_id=paid_membership_request.membership_type_id,
    )

    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_PAID_MEMBER_LIMITS",
        TierLimit(capacity=2, refill_rate=0.0),
    )

    response = await client.get("/healthcheck", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/healthcheck", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/healthcheck", headers=auth_headers)
    assert response.status_code == 429


async def test_admin_rate_limit_exceeds_capacity(
    client: AsyncClient,
    redis_client: Redis,
    admin_auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_ADMIN_LIMITS",
        TierLimit(capacity=2, refill_rate=0.0),
    )

    response = await client.get("/healthcheck", headers=admin_auth_headers)
    assert response.status_code == 200

    response = await client.get("/healthcheck", headers=admin_auth_headers)
    assert response.status_code == 200

    response = await client.get("/healthcheck", headers=admin_auth_headers)
    assert response.status_code == 429


async def test_redis_client_unavailable(
    client: AsyncClient,
    unavailable_redis_client: Redis,
):
    with patch("app.core.utils.rate_limiter.request_logger") as mock_privileges_logger:
        response = await client.get("/healthcheck")

        mock_privileges_logger.error.assert_called_once()

        args, _ = mock_privileges_logger.error.call_args
        log_msg = args[0]

        assert "Rate limiter failed" in log_msg
        assert "9999.9999.9999.9999" in log_msg

        assert response.status_code == 200


async def test_rate_limit_token_refill(
    client: AsyncClient,
    redis_client: Redis,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_GUEST_LIMITS",
        TierLimit(capacity=5, refill_rate=1.0),
    )

    for _ in range(5):
        await client.get("/healthcheck")

    keys = await redis_client.keys("rl:user:*")
    key = keys[0]

    bucket = await redis_client.hgetall(key)
    assert float(bucket['tokens']) < 5.0

    await asyncio.sleep(5)

    await client.get("/healthcheck")

    bucket = await redis_client.hgetall(key)
    assert float(bucket['tokens']) >= 4.0
