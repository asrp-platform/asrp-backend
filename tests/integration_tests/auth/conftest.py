import pytest
from faker import Faker


@pytest.fixture(scope="function")
def login_data(faker: Faker):
    return {
        "email": faker.email(),
        "password": faker.password(),
    }
