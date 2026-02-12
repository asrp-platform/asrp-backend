import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.shared.deps import create_access_token
from app.domains.users.models import ProfessionalInformation, User
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


@pytest.mark.asyncio
async def test_get_professional_information_success(
    client: AsyncClient,
    test_user: User,
    professional_information: ProfessionalInformation,
):
    response = await client.get(f"/api/users/{test_user.id}/professional-information")
    data = response.json()

    assert response.status_code == 200
    assert data["medical_school"] == professional_information.medical_school
    assert data["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_professional_information_user_not_found(
    client: AsyncClient,
):
    response = await client.get("api/users/999999/professional-information")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_professional_information_create_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    faker: Faker,
):
    payload = {
        "medical_school": faker.pystr(max_chars=10),
        "medical_school_country": faker.country(),
        "years_from_to": f"{faker.year()}-{faker.year()}",
        "is_board_certified_pathologist": faker.pybool(),
        "is_us_pathology_trainee": faker.pybool(),
        "is_us_lab_professional": faker.pybool(),
    }

    response = await client.put(
        f"api/users/{test_user.id}/professional-information",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_put_professional_information_forbidden(
    client: AsyncClient,
    test_user: User,
    user_factory: UserFactory,
    faker: Faker,
):
    # создаем другого пользователя
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    payload = {
        "medical_school": faker.pystr(max_chars=10),
        "medical_school_country": faker.country(),
        "years_from_to": f"{faker.year()}-{faker.year()}",
        "is_board_certified_pathologist": faker.pybool(),
        "is_us_pathology_trainee": faker.pybool(),
        "is_us_lab_professional": faker.pybool(),
    }

    response = await client.put(
        f"/api/users/{test_user.id}/professional-information",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )

    assert response.status_code == 403
