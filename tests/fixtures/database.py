from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import TEST_DB_URL
from app.core.database.setup_db import Base
from app.domains.memberships.models import MembershipType


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


@pytest.fixture(scope="session")
async def setup_database(test_engine: AsyncEngine) -> AsyncIterator[None]:
    """Setups database"""
    from app.domains.news.models import News  # noqa raises Mapper initialization errors withot this import
    from app.domains.memberships.models import UserMembership, MembershipType  # noqa

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    async with test_engine.begin() as conn:
        pass
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
