import pytest
from faker import Faker

from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import Fellowship, ProfessionalInformation, Residency, User, UsernameChange


@pytest.fixture(scope="function")
def year_range(faker: Faker) -> str:
    start = faker.random_int(min=1900, max=2100)
    end = faker.random_int(min=1900, max=2100)
    if start > end:
        return f"{end}-{start}"
    return f"{start}-{end}"


@pytest.fixture(scope="function")
async def professional_information(
    user_uow: UserUnitOfWork, test_user: User, faker: Faker, year_range: str
) -> ProfessionalInformation:
    prof_info = await user_uow.professional_information_repository.create(
        user_id=test_user.id,
        medical_school=faker.pystr(min_chars=2),
        medical_school_country=faker.country(),
        years_from_to=year_range,
        is_board_certified_pathologist=True,
        is_us_pathology_trainee=False,
        is_us_lab_professional=False,
    )
    return prof_info


@pytest.fixture(scope="function")
def professional_information_data(faker: Faker, year_range: str) -> dict:
    return {
        "medical_school": faker.pystr(min_chars=2),
        "medical_school_country": faker.country(),
        "years_from_to": year_range,
        "is_board_certified_pathologist": faker.pybool(),
        "is_us_pathology_trainee": faker.pybool(),
        "is_us_lab_professional": faker.pybool(),
    }


@pytest.fixture(scope="function")
async def fellowship(
    user_uow: UserUnitOfWork,
    test_user: User,
    year_range: str,
) -> Fellowship:
    async with user_uow:
        fellowship = await user_uow.fellowship_repository.create(
            user_id=test_user.id,
            institution="Mayo Clinic",
            speciality="Surgical Oncology",
            city="Rochester",
            state="MN",
            country="USA",
            years_from_to=year_range,
        )
    return fellowship


@pytest.fixture(scope="function")
def fellowship_data(
    faker: Faker,
    year_range: str,
) -> dict:
    return {
        "institution": faker.company(),
        "speciality": faker.job(),
        "city": faker.city(),
        "state": faker.state(),
        "country": faker.country(),
        "years_from_to": year_range,
    }


@pytest.fixture(scope="function")
async def residency(
    user_uow: UserUnitOfWork,
    test_user: User,
    year_range: str,
) -> Residency:
    async with user_uow:
        residency = await user_uow.residency_repository.create(
            user_id=test_user.id,
            institution="Johns Hopkins Hospital",
            speciality="Anatomic Pathology",
            city="Baltimore",
            state="MD",
            country="USA",
            years_from_to=year_range,
        )
    return residency


@pytest.fixture(scope="function")
def residency_data(
    faker: Faker,
    year_range: str,
) -> dict:
    return {
        "institution": faker.company(),
        "speciality": faker.job(),
        "city": faker.city(),
        "state": faker.state(),
        "country": faker.country(),
        "years_from_to": year_range,
    }


@pytest.fixture(scope="function")
async def username_change(
    faker: Faker,
    user_uow: UserUnitOfWork,
    test_user: User,
) -> UsernameChange:
    async with user_uow:
        username_change = await user_uow.username_change_repository.create(
            firstname=faker.first_name(),
            lastname=faker.last_name(),
            reason_change=faker.text(max_nb_chars=100),
            user_id=test_user.id
        )
    return username_change


@pytest.fixture(scope="function")
def username_change_data(faker: Faker) -> dict:
    return {
        "firstname": faker.first_name(),
        "lastname": faker.last_name(),
        "reason_change": faker.text(max_nb_chars=100)
    }


@pytest.fixture(scope="function")
def username_reject_change_data(faker: Faker) -> dict:
    return {"reason_rejecting": faker.text(max_nb_chars=100)}
