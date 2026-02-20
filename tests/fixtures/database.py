from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import TEST_DB_URL
from app.core.database.setup_db import Base
from app.domains.permissions.models import Permission


@pytest.fixture(scope="session")
def test_engine() -> AsyncEngine:
    """Creates test engine"""
    return create_async_engine(TEST_DB_URL, echo=True)


@pytest.fixture(scope="session")
def test_session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Returns test session factory"""
    return async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def test_session(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncSession:
    """Yields test session for test database"""
    async with test_session_factory() as session:
        yield session
        # Clear data after single test
        await session.rollback()
        await session.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database(test_engine: AsyncEngine) -> AsyncIterator[None]:
    """Setups database"""
    from app.domains.directors_board.models import DirectorBoardMember  # noqa
    from app.domains.permissions.models import Permission  # noqa
    from app.domains.news.models import News  # noqa raises Mapper initialization errors withot this import because of FK constaraint on User

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
async def insert_test_data(
    setup_database: AsyncIterator[None],
    test_engine: AsyncEngine,
) -> None:
    async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with async_session() as session:
        session.add_all(
            [
                Permission(action="admin.create", name="Assign admin role"),
                Permission(action="admin.view", name="View admin profile"),
                Permission(action="admin.delete", name="Remove admin role"),
                Permission(action="admin.update", name="Update admin profile"),
                Permission(action="permissions.create", name="Create permissions"),
                Permission(action="permissions.view", name="Read permissions"),
                Permission(action="permissions.delete", name="Delete permissions"),
                Permission(action="permissions.update", name="Update permissions"),
                Permission(action="memberships.create", name="Create memberships"),
                Permission(action="memberships.view", name="Read memberships"),
                Permission(action="memberships.delete", name="Delete memberships"),
                Permission(action="memberships.update", name="Update memberships"),
                Permission(action="user_memberships.create", name="Create users memberships"),
                Permission(action="user_memberships.view", name="Read users memberships"),
                Permission(action="user_memberships.delete", name="Delete users memberships"),
                Permission(action="user_memberships.update", name="Update users memberships"),
                Permission(action="director_board.create", name="Create director board members"),
                Permission(action="director_board.view", name="View director board members"),
                Permission(action="director_board.delete", name="Remove director board members"),
                Permission(action="director_board.update", name="Update director board members"),
                Permission(action="feedback.create", name="Assign admin feedback"),
                Permission(action="feedback.view", name="View admin feedback"),
                Permission(action="feedback.delete", name="Remove admin feedback"),
                Permission(action="feedback.update", name="Update admin feedback"),
                Permission(action="legal_documents.create", name="Create legal documents"),
                Permission(action="legal_documents.view", name="View legal documents"),
                Permission(action="legal_documents.update", name="Update legal documents"),
                Permission(action="legal_documents.delete", name="Delete legal documents"),
                Permission(action="username_change.view", name="View username change requests"),
                Permission(action="username_change.update", name="Approve/reject username change requests"),
            ]
        )
        await session.commit()
