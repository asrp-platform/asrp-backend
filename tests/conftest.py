import pytest

from tests.fixtures.auth import *  # noqa
from tests.fixtures.client import *  # noqa
from tests.fixtures.database import *  # noqa
from tests.fixtures.faker import *  # noqa
from tests.fixtures.file_storage import *  # noqa
from tests.fixtures.memberships.membership import *  # noqa
from tests.fixtures.memberships.payloads import *  # noqa
from tests.fixtures.memberships.types import *  # noqa
from tests.fixtures.permissions import *  # noqa
from tests.fixtures.services import *  # noqa
from tests.fixtures.test_transaction_manager import *  # noqa


pytest_plugins = ("anyio",)


@pytest.fixture(scope="session")  # noqa
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _disable_rate_limiter_for_unrelated_tests():
    from app.core.rate_limiter import rate_limiter_dependency
    from app.main import app

    app.dependency_overrides[rate_limiter_dependency] = lambda: None
    yield
    app.dependency_overrides.pop(rate_limiter_dependency, None)


@pytest.fixture(scope="session", autouse=True)
def _cleanup_log_files():
    """Remove test-created log files after the test session to avoid leaving artifacts."""
    yield
    import os

    base = os.getcwd()
    paths = [os.path.join(base, "logs", "privileges.log"), os.path.join(base, "logs", "request_logs.log")]
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
