import pytest
from redis.asyncio import Redis
from redis.backoff import NoBackoff
from redis.client import Retry

from app.core.common.redis_client import get_redis_client
from app.core.config import settings
from app.core.rate_limiter import rate_limiter_dependency
from app.main import app


@pytest.fixture(autouse=True)
def enable_rate_limiter_for_rate_limiter_tests(_disable_rate_limiter_for_unrelated_tests):
    app.dependency_overrides.pop(rate_limiter_dependency, None)


@pytest.fixture(scope="function")
async def test_redis_client():
    test_redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        username=settings.REDIS_USER,
        password=settings.REDIS_USER_PASSWORD,
        db=settings.REDIS_TEST_DB_NUMBER,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        decode_responses=True,
        retry=Retry(backoff=NoBackoff(), retries=0),
    )

    def get_test_redis_client() -> Redis:
        return test_redis_client

    app.dependency_overrides[get_redis_client] = get_test_redis_client

    yield test_redis_client

    await test_redis_client.flushdb()

    app.dependency_overrides.pop(get_redis_client, None)


@pytest.fixture(scope="function")
async def unavailable_test_redis_client():
    test_unavailable_redis_client = Redis(
        host="9999.9999.9999.9999",
        port=settings.REDIS_PORT,
        username=settings.REDIS_USER,
        password=settings.REDIS_USER_PASSWORD,
        db=settings.REDIS_TEST_DB_NUMBER,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        decode_responses=True,
        retry=Retry(backoff=NoBackoff(), retries=0),
    )

    def get_test_redis_client() -> Redis:
        return test_unavailable_redis_client

    app.dependency_overrides[get_redis_client] = get_test_redis_client

    yield test_unavailable_redis_client

    app.dependency_overrides.pop(get_redis_client, None)
