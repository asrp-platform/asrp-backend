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
    test_redis_client: Redis,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_GUEST_LIMITS",
        TierLimit(capacity=2, refill_rate=0.0),
    )

    response = await client.get("/health/ready")
    assert response.status_code == 200

    response = await client.get("/health/ready")
    assert response.status_code == 200

    response = await client.get("/health/ready")
    assert response.status_code == 429


async def test_authenticated_rate_limit_exceeds_capacity(
    client: AsyncClient,
    test_redis_client: Redis,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_AUTHENTICATED_LIMITS",
        TierLimit(capacity=2, refill_rate=0.0),
    )

    response = await client.get("/health/ready", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/health/ready", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/health/ready", headers=auth_headers)
    assert response.status_code == 429


async def test_paid_member_rate_limit_exceeds_capacity(
    client: AsyncClient,
    test_redis_client: Redis,
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

    response = await client.get("/health/ready", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/health/ready", headers=auth_headers)
    assert response.status_code == 200

    response = await client.get("/health/ready", headers=auth_headers)
    assert response.status_code == 429


async def test_admin_rate_limit_exceeds_capacity(
    client: AsyncClient,
    test_redis_client: Redis,
    admin_auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_ADMIN_LIMITS",
        TierLimit(capacity=2, refill_rate=0.0),
    )

    response = await client.get("/health/ready", headers=admin_auth_headers)
    assert response.status_code == 200

    response = await client.get("/health/ready", headers=admin_auth_headers)
    assert response.status_code == 200

    response = await client.get("/health/ready", headers=admin_auth_headers)
    assert response.status_code == 429


async def test_test_redis_client_unavailable(
    client: AsyncClient,
    unavailable_test_redis_client: Redis,
):
    with patch("app.core.rate_limiter.logger") as mock_logger:
        response = await client.get("/health/ready")

        mock_logger.error.assert_called_once()

        args, _ = mock_logger.error.call_args
        log_msg = args[0]

        assert "Rate limiter failed" in log_msg

        assert response.status_code == 200


async def test_rate_limit_token_refill(
    client: AsyncClient,
    test_redis_client: Redis,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "RATE_LIMITER_GUEST_LIMITS",
        TierLimit(capacity=5, refill_rate=1.0),
    )

    for _ in range(5):
        await client.get("/health/ready")

    keys = await test_redis_client.keys("rl:user:*")
    key = keys[0]

    bucket = await test_redis_client.hgetall(key)
    assert float(bucket["tokens"]) < 5.0

    await asyncio.sleep(5)

    await client.get("/health/ready")

    bucket = await test_redis_client.hgetall(key)
    assert float(bucket["tokens"]) >= 4.0
