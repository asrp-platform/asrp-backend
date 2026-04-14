import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_access_token
from app.domains.users.infrastructure import UserTransactionManagerBase
from app.domains.users.models import Fellowship, Residency, User
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


@pytest.mark.asyncio
async def test_get_user_residencies_success(
    client: AsyncClient,
    test_user: User,
    residency: Residency,
):
    response = await client.get(f"/api/users/{test_user.id}/residencies")

    data = response.json()

    assert response.status_code == 200
    assert data[0]["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_user_residencies_user_not_found(
    client: AsyncClient,
):
    response = await client.get("/api/users/999999/residencies")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_single_user_residency_success(
    client: AsyncClient,
    test_user: User,
    residency: Residency,
):
    response = await client.get(f"/api/users/{test_user.id}/residencies/{residency.id}")

    data = response.json()

    assert response.status_code == 200
    assert data["id"] == residency.id
    assert data["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_single_user_residency_not_found(
    client: AsyncClient,
    test_user: User,
):
    response = await client.get(f"/api/users/{test_user.id}/residencies/999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_residency_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    residency_data: dict,
):
    response = await client.post(
        f"/api/users/{test_user.id}/residencies",
        headers=auth_headers,
        json=residency_data,
    )

    data = response.json()

    assert response.status_code == 201
    assert data["institution"] == residency_data["institution"]
    assert data["speciality"] == residency_data["speciality"]
    assert data["user_id"] == test_user.id


async def test_create_user_residency_not_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    residency_data: dict,
):
    async with user_uow:
        await user_uow.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    response = await client.post(
        f"/api/users/{test_user.id}/residencies",
        headers=auth_headers,
        json=residency_data,
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_user_residency_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    residency: Residency,
    residency_data: dict,
):
    async with user_uow:
        await user_uow.residency_repository.update(
            residency.id,
            current_position=True,
        )

    residency_data["current_position"] = True

    response = await client.post(
        f"/api/users/{test_user.id}/residencies",
        headers=auth_headers,
        json=residency_data,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_user_residency_forbidden(
    client: AsyncClient,
    test_user: User,
    user_factory: UserFactory,
    residency_data: dict,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.post(
        f"/api/users/{test_user.id}/residencies",
        headers={"Authorization": f"Bearer {access_token}"},
        json=residency_data,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_residency_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    residency: Residency,
    residency_data: dict,
):
    response = await client.put(
        f"/api/users/{test_user.id}/residencies/{residency.id}",
        headers=auth_headers,
        json=residency_data,
    )

    data = response.json()

    assert response.status_code == 200
    assert data["institution"] == residency_data["institution"]
    assert data["speciality"] == residency_data["speciality"]


async def test_update_user_residency_current_position(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    residency: Residency,
    residency_data: dict,
):
    async with user_uow:
        await user_uow.residency_repository.update(
            residency.id,
            current_position=True,
        )

    response = await client.put(
        f"/api/users/{test_user.id}/residencies/{residency.id}",
        headers=auth_headers,
        json=residency_data,
    )

    assert response.status_code == 200


async def test_update_user_residency_current_position_professional_experience_current_position_not_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    residency: Residency,
    residency_data: dict,
):
    residency_data["current_position"] = True

    response = await client.put(
        f"/api/users/{test_user.id}/residencies/{residency.id}",
        headers=auth_headers,
        json=residency_data,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_user_residency_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    residency: Residency,
    fellowship: Fellowship,
    residency_data: dict,
):
    async with user_uow:
        await user_uow.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    residency_data["current_position"] = True

    response = await client.put(
        f"/api/users/{test_user.id}/residencies/{residency.id}",
        headers=auth_headers,
        json=residency_data,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_user_residency_forbidden(
    client: AsyncClient,
    test_user: User,
    residency: Residency,
    user_factory: UserFactory,
    residency_data: dict,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.put(
        f"/api/users/{test_user.id}/residencies/{residency.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=residency_data,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_residency_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    residency: Residency,
    user_uow,
    year_range: str,
):
    # ensure there are at least two residencies so deleting one is allowed
    async with user_uow:
        await user_uow.residency_repository.create(
            user_id=test_user.id,
            institution="Another Institution",
            speciality="Another Speciality",
            city="City",
            state="ST",
            country="Country",
            years_from_to=year_range,
        )

    response = await client.delete(
        f"/api/users/{test_user.id}/residencies/{residency.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_user_residency_not_found(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
):
    response = await client.delete(
        f"/api/users/{test_user.id}/residencies/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_residency_cannot_delete_last(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    residency: Residency,
):
    response = await client.delete(
        f"/api/users/{test_user.id}/residencies/{residency.id}",
        headers=auth_headers,
    )

    assert response.status_code == 409
