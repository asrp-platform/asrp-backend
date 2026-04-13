from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import TEST_DB_URL
from app.core.database.setup_db import Base
from app.domains.memberships.models import MembershipType
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
    from app.domains.payments.models import Payment  # noqa raises Mapper initialization errors withot this import because of FK constaraint on User

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
                Permission(action="name_change_request.view", name="View name change requests"),
                Permission(action="name_change_request.update", name="Approve/reject name change requests"),
                Permission(action="name_change_request.create", name="Create name change requests"),
                Permission(action="name_change_request.delete", name="Delete name change requests"),

                MembershipType(
                    name="Active Member",
                    type="ACTIVE",
                    price_usd=20.00,
                    duration=365,
                    description="Any legally qualified Russian-speaking specialist (MD, DO, MBBS, PhD, or equivalent degree). practicing pathology in the united states",
                    is_purchasable=True,
                ),
                MembershipType(
                    name="Trainee Member",
                    type="TRAINEE",
                    price_usd=20.00,
                    duration=365,
                    description="Russian-speaking residents or fellows in pathology or related disciplines in the United States.",
                    is_purchasable=True,
                ),
                MembershipType(
                    name="Affiliate Member",
                    type="AFFILIATE",
                    price_usd=20.00,
                    duration=365,
                    description="Russian-speaking pathologists, scientists, researchers, or allied professionals interested in the field of pathology whose involvement is relevant and contributes meaningfully to the Society (non-voting).",
                    is_purchasable=True,
                ),
                MembershipType(
                    name="Honorary Member",
                    type="HONORARY",
                    price_usd=20.00,
                    duration=365,
                    description="Individuals recognized fo exceptional service to the field of pathology or the Society (non-voting).",
                    is_purchasable=False,
                ),
                MembershipType(
                    name="Pathway Member",
                    type="PATHWAY",
                    price_usd=20.00,
                    duration=365,
                    description="Russian-speaking individuals pursuing or transition into a medical career in the United States. This includes medical students and internationally trained medical graduates seeking mentorship and professional development as they prepare for pathology practice in the United States (non-voting).",
                    is_purchasable=True,
                ),
            ]
        )
        await session.commit()
