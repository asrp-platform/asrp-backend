from datetime import date
from io import BytesIO

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.content.models import CaseOfTheMonth, CaseTag
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def create_case(
    transaction_manager: TransactionManager,
    faker: Faker,
    *,
    tags: list[CaseTag] | None = None,
) -> CaseOfTheMonth:
    case = await transaction_manager.case_of_the_month_repository.create(
        title=faker.sentence(),
        history={"type": "doc", "content": []},
        case_findings={"type": "doc", "content": []},
        virtual_slides=[],
        questions=[faker.sentence()],
        publication_month=date(2026, 10, 1),
        answer={"type": "doc", "content": []},
    )
    if tags is not None:
        case.tags = tags
    await transaction_manager.flush()
    return case


async def test_public_cases_can_be_filtered_by_one_tag(
    client: AsyncClient,
    faker: Faker,
    test_transaction_manager: TransactionManager,
) -> None:
    async with test_transaction_manager:
        tag = await test_transaction_manager.case_tag_repository.create(name=faker.unique.word())
        matching_case = await create_case(test_transaction_manager, faker, tags=[tag])
        other_case = await create_case(test_transaction_manager, faker)
        matching_case_id = matching_case.id
        other_case_id = other_case.id
        tag_id = tag.id

    response = await client.get(
        "/api/case-of-the-month/cases",
        params={"tag_id": tag_id, "page": 1, "page_size": 25},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert [item["id"] for item in response.json()["data"]] == [matching_case_id]
    assert other_case_id not in {item["id"] for item in response.json()["data"]}


async def test_public_case_detail_hides_soft_deleted_tags_and_deleted_tag_filter_matches_nothing(
    client: AsyncClient,
    faker: Faker,
    test_session,
    test_transaction_manager: TransactionManager,
) -> None:
    async with test_transaction_manager:
        tag = await test_transaction_manager.case_tag_repository.create(name=faker.unique.word())
        case = await create_case(test_transaction_manager, faker, tags=[tag])
        case_slug = case.slug
        tag_id = tag.id

        await test_transaction_manager.case_tag_repository.mark_as_deleted(tag_id)

    test_session.expire_all()

    detail_response = await client.get(f"/api/case-of-the-month/cases/{case_slug}")
    filtered_response = await client.get(
        "/api/case-of-the-month/cases",
        params={"tag_id": tag_id, "page": 1, "page_size": 25},
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["tags"] == []
    assert filtered_response.status_code == 200
    assert filtered_response.json()["count"] == 0
    assert filtered_response.json()["data"] == []


async def test_public_missing_case_slug_returns_slug_error(client: AsyncClient) -> None:
    response = await client.get("/api/case-of-the-month/cases/missing-case-slug")

    assert response.status_code == 404
    assert response.json()["detail"] == "Case of the month with provided slug not found"


async def test_admin_case_tag_crud_uses_case_of_the_month_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    faker: Faker,
) -> None:
    response = await client.post(
        "/api/admin/case-of-the-month/tags",
        headers=admin_auth_headers,
        json={"name": faker.unique.word()},
    )

    assert response.status_code == 201
    tag_id = response.json()["id"]

    get_response = await client.get(
        f"/api/admin/case-of-the-month/tags/{tag_id}",
        headers=admin_auth_headers,
    )
    assert get_response.status_code == 200

    update_response = await client.patch(
        f"/api/admin/case-of-the-month/tags/{tag_id}",
        headers=admin_auth_headers,
        json={"name": faker.unique.word()},
    )
    assert update_response.status_code == 200

    delete_response = await client.delete(
        f"/api/admin/case-of-the-month/tags/{tag_id}",
        headers=admin_auth_headers,
    )
    assert delete_response.status_code == 204


async def test_admin_case_tags_without_case_of_the_month_permission_return_403(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get("/api/admin/case-of-the-month/tags", headers=admin_auth_headers)

    assert response.status_code == 403


async def test_admin_cannot_delete_case_tag_used_by_active_case(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    faker: Faker,
    test_transaction_manager: TransactionManager,
) -> None:
    async with test_transaction_manager:
        tag = await test_transaction_manager.case_tag_repository.create(name=faker.unique.word())
        await create_case(test_transaction_manager, faker, tags=[tag])
        tag_id = tag.id

    response = await client.delete(
        f"/api/admin/case-of-the-month/tags/{tag_id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Case tag cannot be deleted because it is used by cases"


async def test_admin_case_of_the_month_image_upload(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    spy_file_storage,
) -> None:
    response = await client.post(
        "/api/admin/case-of-the-month/images",
        headers=admin_auth_headers,
        files={"file": ("slide.png", BytesIO(b"image"), "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["object_key"].startswith("case-of-the-month/")
    spy_file_storage["upload_file"].assert_awaited_once()
