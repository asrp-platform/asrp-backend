import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_access_token
from app.domains.users.infrastructure import UserTransactionManagerBase
from app.domains.users.models import Fellowship, Job, User
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


@pytest.mark.asyncio
async def test_get_user_fellowships_success(
    client: AsyncClient,
    test_user: User,
    fellowship: Fellowship,
    user_uow: UserTransactionManagerBase,
):
    response = await client.get(f"/api/users/{test_user.id}/fellowships")

    data = response.json()

    assert response.status_code == 200
    assert data[0]["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_user_fellowships_user_not_found(
    client: AsyncClient,
):
    response = await client.get("/api/users/999999/fellowships")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_single_user_fellowship_success(
    client: AsyncClient,
    test_user: User,
    fellowship: Fellowship,
):
    response = await client.get(f"/api/users/{test_user.id}/fellowships/{fellowship.id}")

    data = response.json()

    assert response.status_code == 200
    assert data["id"] == fellowship.id
    assert data["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_get_single_user_fellowship_not_found(
    client: AsyncClient,
    test_user: User,
):
    response = await client.get(f"/api/users/{test_user.id}/fellowships/999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_fellowship_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    fellowship_data: dict,
):
    response = await client.post(
        f"/api/users/{test_user.id}/fellowships",
        headers=auth_headers,
        json=fellowship_data,
    )

    data = response.json()

    assert response.status_code == 201
    assert data["institution"] == fellowship_data["institution"]
    assert data["speciality"] == fellowship_data["speciality"]
    assert data["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_create_user_fellowship_not_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    fellowship_data: dict,
):
    async with user_uow:
        await user_uow.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    response = await client.post(
        f"/api/users/{test_user.id}/fellowships",
        headers=auth_headers,
        json=fellowship_data,
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_user_fellowship_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    fellowship_data: dict,
):
    async with user_uow:
        await user_uow.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    fellowship_data["current_position"] = True

    response = await client.post(
        f"/api/users/{test_user.id}/fellowships",
        headers=auth_headers,
        json=fellowship_data,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_user_fellowship_forbidden(
    client: AsyncClient,
    test_user: User,
    user_factory: UserFactory,
    fellowship_data: dict,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.post(
        f"/api/users/{test_user.id}/fellowships",
        headers={"Authorization": f"Bearer {access_token}"},
        json=fellowship_data,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_fellowship_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    fellowship: Fellowship,
    fellowship_data: dict,
):
    response = await client.put(
        f"/api/users/{test_user.id}/fellowships/{fellowship.id}",
        headers=auth_headers,
        json=fellowship_data,
    )

    data = response.json()

    assert response.status_code == 200
    assert data["institution"] == fellowship_data["institution"]
    assert data["speciality"] == fellowship_data["speciality"]


@pytest.mark.asyncio
async def test_update_user_fellowship_current_position(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    fellowship_data: dict,
):
    async with user_uow:
        await user_uow.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    response = await client.put(
        f"/api/users/{test_user.id}/fellowships/{fellowship.id}",
        headers=auth_headers,
        json=fellowship_data,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_user_fellowship_current_position_professional_experience_current_position_not_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    fellowship_data: dict,
):
    fellowship_data["current_position"] = True

    response = await client.put(
        f"/api/users/{test_user.id}/fellowships/{fellowship.id}",
        headers=auth_headers,
        json=fellowship_data,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_user_fellowship_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    job: Job,
    fellowship_data: dict,
):
    async with user_uow:
        await user_uow.job_repository.update(
            job.id,
            current_position=True,
        )

    fellowship_data["current_position"] = True

    response = await client.put(
        f"/api/users/{test_user.id}/fellowships/{fellowship.id}",
        headers=auth_headers,
        json=fellowship_data,
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_user_fellowship_forbidden(
    client: AsyncClient,
    test_user: User,
    fellowship: Fellowship,
    user_factory: UserFactory,
    fellowship_data: dict,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.put(
        f"/api/users/{test_user.id}/fellowships/{fellowship.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=fellowship_data,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_fellowship_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    fellowship: Fellowship,
):
    response = await client.delete(
        f"/api/users/{test_user.id}/fellowships/{fellowship.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_user_fellowship_not_found(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
):
    response = await client.delete(
        f"/api/users/{test_user.id}/fellowships/999999",
        headers=auth_headers,
    )

    assert response.status_code == 404
