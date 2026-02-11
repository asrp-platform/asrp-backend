import pytest

from app.domains.users.models import ProfessionalInformation, User

pytestmark = pytest.mark.anyio


@pytest.mark.asyncio
async def test_get_professional_information_success(
    client,
    test_user: User,
    professional_information: ProfessionalInformation,
):
    response = await client.get(f"/api/users/{test_user.id}/professional-information")
    data = response.json()

    assert response.status_code == 200
    assert data["medical_school"] == professional_information.medical_school
    assert data["user_id"] == test_user.id


# @pytest.mark.asyncio
# async def test_get_professional_information_user_not_found(
#     client,
# ):
#     response = await client.get(
#         "/users/999999/professional-information"
#     )
#
#     assert response.status_code == 404
#
#
# @pytest.mark.asyncio
# async def test_put_professional_information_create_success(
#     async_client,
#     test_user,
#     override_current_user,
# ):
#     payload = {
#         "medical_school": "Mayo Clinic",
#         "medical_school_country": "USA",
#         "years_from_to": "2015–2019",
#         "is_board_certified_pathologist": False,
#         "is_us_pathology_trainee": True,
#         "is_us_lab_professional": False,
#     }
#
#     response = await async_client.put(
#         f"/users/{test_user.id}/professional-information",
#         json=payload,
#     )
#
#     assert response.status_code == HTTPStatus.OK
#     data = response.json()
#     assert data["medical_school"] == payload["medical_school"]
#     assert data["is_us_pathology_trainee"] is True
#
#
# @pytest.mark.asyncio
# async def test_put_professional_information_forbidden(
#     async_client,
#     test_user,
#     user_uow,
#     faker_instance,
# ):
#     # создаем другого пользователя
#     another_user = await user_uow.user_repository.create(
#         firstname=faker_instance.first_name(),
#         lastname=faker_instance.last_name(),
#         email=faker_instance.email(),
#         password="1234",
#         stuff=False,
#         country="USA",
#         city="NY",
#         institution="Test",
#         role="doctor",
#     )
#
#     # override current_user = другой пользователь
#     async def override():
#         return another_user
#
#     from app.domains.shared.deps import get_current_user
#     from app.main import app
#
#     app.dependency_overrides[get_current_user] = override
#
#     payload = {
#         "medical_school": "Stanford",
#         "medical_school_country": "USA",
#         "years_from_to": "2010–2014",
#         "is_board_certified_pathologist": False,
#         "is_us_pathology_trainee": False,
#         "is_us_lab_professional": True,
#     }
#
#     response = await async_client.put(
#         f"/users/{test_user.id}/professional-information",
#         json=payload,
#     )
#
#     assert response.status_code == HTTPStatus.FORBIDDEN
#
#     app.dependency_overrides.clear()
