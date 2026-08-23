from datetime import datetime

import pytest
from httpx import AsyncClient

from app.domains.memberships.models import MembershipType, UserMembership
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def test_get_membership_confirmation(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    purchasable_membership_type: MembershipType,
    user_membership: UserMembership,
) -> None:
    response = await client.get(
        "/api/users/current-user/membership/confirmation",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data == {
        "member_name": test_user.full_name,
        "membership_type": purchasable_membership_type.type.value,
        "membership_id": f"ASRP-{user_membership.created_at.year}-{user_membership.id:05d}",
        "valid_through": data["valid_through"],
    }
    assert _parse_datetime(data["valid_through"]) == user_membership.expires_at


async def test_get_membership_confirmation_without_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/users/current-user/membership/confirmation",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Membership for the current user not found"


async def test_get_membership_confirmation_returns_only_modal_fields(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    user_membership: UserMembership,
) -> None:
    response = await client.get(
        "/api/users/current-user/membership/confirmation",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert set(response.json()) == {
        "member_name",
        "membership_type",
        "membership_id",
        "valid_through",
    }


async def test_get_membership_confirmation_pdf(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    user_membership: UserMembership,
) -> None:
    membership_id = f"ASRP-{user_membership.created_at.year}-{user_membership.id:05d}"

    response = await client.get(
        "/api/users/current-user/membership/confirmation/pdf",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="membership-confirmation-{membership_id}.pdf"'
    )
    assert response.content.startswith(b"%PDF")


async def test_membership_confirmation_pdf_openapi_contract(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/users/current-user/membership/confirmation/pdf"]["get"]
    success_response = operation["responses"]["200"]

    assert success_response["content"] == {
        "application/pdf": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert "Content-Disposition" in success_response["headers"]
    assert "responseType" in operation["description"]


async def test_membership_confirmation_pdf_exposes_filename_header(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    user_membership: UserMembership,
) -> None:
    response = await client.get(
        "/api/users/current-user/membership/confirmation/pdf",
        headers={**auth_headers, "Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-expose-headers"] == "Content-Disposition"
