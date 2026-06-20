import pytest
from faker import Faker


pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def faker() -> Faker:
    fake = Faker()
    yield fake
