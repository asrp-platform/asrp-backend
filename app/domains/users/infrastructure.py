from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.users.models import ProfessionalInformation, User


class UserRepository(SQLAlchemyRepository):
    model = User


class ProfessionalInformationRepository(SQLAlchemyRepository):
    model = ProfessionalInformation


class UserUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)
        self.professional_information_repository = ProfessionalInformationRepository(self._session)


def get_user_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> UserUnitOfWork:
    return UserUnitOfWork(session)
