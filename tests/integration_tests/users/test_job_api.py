import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_access_token
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import Fellowship, Job, User
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


async def test_get_user_jobs_success(
    client: AsyncClient,
    test_user: User,
    job: Job,
):
    response = await client.get(f"/api/users/{test_user.id}/jobs")

    assert response.status_code == 200
    assert response.json()[0]["user_id"] == test_user.id


async def test_get_user_jobs_user_not_found(
    client: AsyncClient,
    test_user: User,
    job: Job,
):
    response = await client.get(f"/api/users/{99999999}/jobs")

    assert response.status_code == 404


async def test_get_single_user_job_success(
    client: AsyncClient,
    test_user: User,
    job: Job,
):
    response = await client.get(f"/api/users/{test_user.id}/jobs/{job.id}")

    assert response.status_code == 200
    assert response.json()["user_id"] == test_user.id
    assert response.json()["id"] == job.id


async def test_get_single_user_job_not_found(
    client: AsyncClient,
    test_user: User,
    job: Job,
):
    response = await client.get(f"/api/users/{test_user.id}/jobs/{9999999}")

    assert response.status_code == 404


async def test_get_single_user_job_user_not_found(
    client: AsyncClient,
    test_user: User,
    job: Job,
):
    response = await client.get(f"/api/users/{9999999}/jobs/{job.id}")

    assert response.status_code == 404


async def test_create_user_job_success(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    job_data: dict,
):
    response = await client.post(
        f"/api/users/{test_user.id}/jobs",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == test_user.id
    assert response.json()["institution"] == job_data["institution"]


async def test_create_user_job_forbidden(
    client: AsyncClient,
    user_factory: UserFactory,
    test_user: User,
    job_data: dict,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.post(
        f"/api/users/{test_user.id}/jobs",
        headers={"Authorization": f"Bearer {access_token}"},
        json=job_data,
    )

    assert response.status_code == 403


async def test_create_user_job_not_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    job_data: dict,
):
    async with test_transaction_manager:
        await test_transaction_manager.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    response = await client.post(
        f"/api/users/{test_user.id}/jobs",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 201


async def test_create_user_job_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    job_data: dict,
):
    async with test_transaction_manager:
        await test_transaction_manager.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    job_data["current_position"] = True

    response = await client.post(
        f"/api/users/{test_user.id}/jobs",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 409


async def test_update_user_job_success(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    job: Job,
    job_data: dict,
):
    response = await client.put(
        f"/api/users/{test_user.id}/jobs/{job.id}",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == test_user.id
    assert response.json()["institution"] == job_data["institution"]
    assert response.json()["speciality"] == job_data["speciality"]


async def test_update_user_job_not_found(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    job: Job,
    job_data: dict,
):
    response = await client.put(
        f"/api/users/{test_user.id}/jobs/{9999999}",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 404


async def test_update_user_job_forbidden(
    client: AsyncClient,
    user_factory: UserFactory,
    test_user: User,
    job: Job,
    job_data: dict,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.put(
        f"/api/users/{test_user.id}/jobs/{job.id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=job_data,
    )

    assert response.status_code == 403


async def test_update_user_job_current_position(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    auth_headers: AuthHeaders,
    test_user: User,
    job: Job,
    job_data: dict,
):
    async with test_transaction_manager:
        await test_transaction_manager.job_repository.update(
            job.id,
            current_position=True,
        )

    response = await client.put(
        f"/api/users/{test_user.id}/jobs/{job.id}",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 200


async def test_update_user_job_current_position_professional_experience_current_position_not_exists(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    job: Job,
    job_data: dict,
):
    job_data["current_position"] = True

    response = await client.put(
        f"/api/users/{test_user.id}/jobs/{job.id}",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 200


async def test_update_user_job_current_position_professional_experience_current_position_already_exists(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    auth_headers: AuthHeaders,
    test_user: User,
    fellowship: Fellowship,
    job: Job,
    job_data: dict,
):
    async with test_transaction_manager:
        await test_transaction_manager.fellowship_repository.update(
            fellowship.id,
            current_position=True,
        )

    job_data["current_position"] = True

    response = await client.put(
        f"/api/users/{test_user.id}/jobs/{job.id}",
        headers=auth_headers,
        json=job_data,
    )

    assert response.status_code == 409


async def test_delete_user_job_success(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    job: Job,
):
    response = await client.delete(
        f"/api/users/{test_user.id}/jobs/{job.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200


async def test_delete_user_job_forbidden(
    client: AsyncClient,
    user_factory: UserFactory,
    test_user: User,
    job: Job,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    response = await client.delete(
        f"/api/users/{test_user.id}/jobs/{job.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403


async def test_delete_user_job_not_found(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    job: Job,
):
    response = await client.delete(
        f"/api/users/{test_user.id}/jobs/{9999999}",
        headers=auth_headers,
    )

    assert response.status_code == 404
