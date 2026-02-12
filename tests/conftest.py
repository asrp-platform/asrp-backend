from tests.fixtures.client import *  # noqa
from tests.fixtures.faker import *  # noqa
from tests.fixtures.database import *  # noqa
from tests.fixtures.uow import *  # noqa
from tests.fixtures.auth import *  # noqa
from tests.fixtures.permissions import *  # noqa


pytest_plugins = ("anyio",)


@pytest.fixture(scope="session")  # noqa
def anyio_backend() -> str:
    return "asyncio"
