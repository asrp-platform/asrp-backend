import pytest
from faker import Faker

from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import Fellowship, ProfessionalInformation, Residency, User


@pytest.fixture(scope="function")
def year_range(faker: Faker) -> str:
    start = int(faker.year())
    end = int(faker.year())
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
def professional_information_data(faker: Faker) -> dict:
    return {
        "medical_school": faker.pystr(min_chars=2),
        "medical_school_country": faker.country(),
        "years_from_to": f"{faker.year()}-{faker.year()}",
        "is_board_certified_pathologist": faker.pybool(),
        "is_us_pathology_trainee": faker.pybool(),
        "is_us_lab_professional": faker.pybool(),
    }


@pytest.fixture(scope="function")
async def fellowship(
    user_uow: UserUnitOfWork,
    test_user: User,
) -> Fellowship:
    async with user_uow:
        fellowship = await user_uow.fellowship_repository.create(
            user_id=test_user.id,
            institution="Mayo Clinic",
            speciality="Surgical Oncology",
            city="Rochester",
            state="MN",
            country="USA",
            years_from_to="2015-2017",
        )
    return fellowship


@pytest.fixture(scope="function")
def fellowship_data(faker: Faker) -> dict:
    return {
        "institution": faker.company(),
        "speciality": faker.job(),
        "city": faker.city(),
        "state": faker.state(),
        "country": faker.country(),
        "years_from_to": "2015-2017",
    }


@pytest.fixture(scope="function")
async def residency(
    user_uow: UserUnitOfWork,
    test_user: User,
) -> Residency:
    async with user_uow:
        residency = await user_uow.residency_repository.create(
            user_id=test_user.id,
            institution="Johns Hopkins Hospital",
            speciality="Anatomic Pathology",
            city="Baltimore",
            state="MD",
            country="USA",
            years_from_to="2010-2014",
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
