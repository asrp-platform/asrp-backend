import pytest

from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import ProfessionalInformation, User


@pytest.fixture(scope="function")
async def professional_information(
    user_uow: UserUnitOfWork,
    test_user: User,
) -> ProfessionalInformation:
    prof_info = await user_uow.professional_information_repository.create(
        user_id=test_user.id,
        medical_school="Harvard Medical School",
        medical_school_country="USA",
        years_from_to="2010–2014",
        is_board_certified_pathologist=True,
        is_us_pathology_trainee=False,
        is_us_lab_professional=False,
    )
    return prof_info
