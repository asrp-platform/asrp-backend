import time
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.core.logging import REQUESTS_CHANNEL, configure_logging
from app.core.utils.redis_client import RedisClientDep
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.shared.deps import access_token_header, get_email_by_access_token
from app.domains.users.services import UserServiceDep


configure_logging()
request_logger = logger.bind(channel=REQUESTS_CHANNEL)


class RateLimiter:
    REQUEST_COST: int = 1

    def __init__(
            self,
            user_ip: str,
            capacity: float,
            refill_rate: float,
            key_ttl: int,
            redis_client: Redis
    ):
        self.key = f"rl:user:{user_ip}"
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.key_ttl = key_ttl

        self.redis_client = redis_client

    async def check_limit(self) -> bool:
        bucket = await self.redis_client.hgetall(self.key)
        now = time.time()

        if not bucket:
            tokens = self.capacity
            last_refill = now
        else:
            tokens = float(bucket["tokens"])
            last_refill = float(bucket["last_refill"])

        # calculation of available tokens
        elapsed = now - last_refill
        refill = elapsed * self.refill_rate
        tokens = min(self.capacity, tokens + refill)

        if tokens >= self.REQUEST_COST:
            tokens = tokens - self.REQUEST_COST

            await self.redis_client.hset(
                self.key,
                mapping={
                    "tokens": tokens,
                    "last_refill": now,
                }
            )
            await self.redis_client.expire(self.key, self.key_ttl)
            return True
        return False


async def rate_limiter_dependency(
    request: Request,
    user_service: UserServiceDep,
    user_membership_service: UserMembershipServiceDep,
    redis_client: RedisClientDep,
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(access_token_header)],
) -> None:
    if access_token is None:
        user = None
    else:
        email = get_email_by_access_token(access_token)
        user = await user_service.get_user_by_kwargs(email=email)

    if user is not None:
        user_membership = await user_membership_service.get_user_membership_by_user_id(user.id)

        if user.admin:
            capacity = settings.RATE_LIMITER_ADMIN_LIMITS.capacity
            refill_rate = settings.RATE_LIMITER_ADMIN_LIMITS.refill_rate

        elif user_membership is not None:
            capacity = settings.RATE_LIMITER_PAID_MEMBER_LIMITS.capacity
            refill_rate = settings.RATE_LIMITER_PAID_MEMBER_LIMITS.refill_rate

        else:
            capacity = settings.RATE_LIMITER_AUTHENTICATED_LIMITS.capacity
            refill_rate = settings.RATE_LIMITER_AUTHENTICATED_LIMITS.refill_rate

    else:
        capacity = settings.RATE_LIMITER_GUEST_LIMITS.capacity
        refill_rate = settings.RATE_LIMITER_GUEST_LIMITS.refill_rate

    ip = request.client.host

    rate_limiter = RateLimiter(
        user_ip=ip,
        capacity=capacity,
        refill_rate=refill_rate,
        key_ttl=settings.RATE_LIMITER_KEY_TTL,
        redis_client=redis_client,
    )

    try:
        if not await rate_limiter.check_limit():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
    except (ConnectionError, TimeoutError) as error:
        request_logger.error(
            f"Rate limiter failed while checking request limit due to Redis connection issue. Error: {error}"
        )
