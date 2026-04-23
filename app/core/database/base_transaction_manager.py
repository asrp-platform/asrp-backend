from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.setup_db import session_factory


class BaseTransactionManager(ABC):
    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    @abstractmethod
    async def rollback(self): ...

    @abstractmethod
    async def commit(self): ...


class SQLAlchemyTransactionManagerBase(BaseTransactionManager):
    def __init__(self, session: AsyncSession = None):
        self._session = session or session_factory()

    async def __aenter__(self):
        return self  # Возвращает сам объект, чтобы можно было использовать внутри контекстного менеджера async with

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:  # тип ошибки, если она произошла
            await self.rollback()
        else:
            await self.commit()

        await self._session.close()

    async def rollback(self):
        await self._session.rollback()

    async def commit(self):
        await self._session.commit()
