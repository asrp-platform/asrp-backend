import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_access_token
from app.domains.users.models import ProfessionalInformation, User
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


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


async def test_get_professional_information_success_none(
    client: AsyncClient,
    test_user: User,
):
    response = await client.get(f"/api/users/{test_user.id}/professional-information")
    data = response.json()

    assert response.status_code == 200
    assert data is None


async def test_get_professional_information_user_not_found(
    client: AsyncClient,
):
    response = await client.get("api/users/999999/professional-information")

    assert response.status_code == 404


async def test_put_professional_information_create_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    professional_information_data: dict,
):
    response = await client.put(
        f"api/users/{test_user.id}/professional-information",
        headers=auth_headers,
        json=professional_information_data,
    )

    assert response.status_code == 200


async def test_put_professional_information_forbidden(
    client: AsyncClient,
    test_user: User,
    user_factory: UserFactory,
    professional_information_data: dict,
):
    # создаем другого пользователя
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.put(
        f"/api/users/{test_user.id}/professional-information",
        headers={"Authorization": f"Bearer {access_token}"},
        json=professional_information_data,
    )

    assert response.status_code == 403
