import pytest
from typing import Any
from faker import Faker
from unittest.mock import AsyncMock, patch

import app.core.config

from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.core.storage.base_storage import S3BaseStorage
from app.domains.directors_board.infrastructure import DirectorsBoardMemberUnitOfWork
from app.domains.directors_board.models import DirectorBoardMember


@pytest.fixture()
def mock_s3_storage():
    """
    Robustly mocks S3BaseStorage methods globally at the class level.
    Now that volume mounts are fixed, this will correctly intercept calls
    from any instance of S3BaseStorage in the app.
    """
    with (
        patch.object(S3BaseStorage, "delete_object", new_callable=AsyncMock) as mock_delete,
        patch.object(S3BaseStorage, "upload_file", new_callable=AsyncMock) as mock_upload,
        patch.object(S3BaseStorage, "get_presigned_object", new_callable=AsyncMock) as mock_get_presigned,
    ):
        # Default mock behavior
        mock_get_presigned.return_value = "http://fake-s3-url.com/image.jpg"

        # Create a helper object to track calls in tests
        mocked = AsyncMock()
        mocked.delete_object = mock_delete
        mocked.upload_file = mock_upload
        mocked.get_presigned_object = mock_get_presigned
        yield mocked


@pytest.fixture(scope="function")
async def directors_board_member_data(faker: Faker) -> dict[str, Any]:
    return {
        "role": faker.pystr(),
        "name": faker.name(),
        "content": faker.pydict(),
    }


@pytest.fixture(scope="function")
async def directors_board_member_db(
    faker: Faker, directors_board_uow: DirectorsBoardMemberUnitOfWork, directors_board_member_data: dict[str, Any]
) -> DirectorBoardMember:
    creation_data = {
        "role": faker.job(),
        "name": faker.name(),
        "photo_url": faker.image_url(),
        "content": {
            "bio": faker.paragraph(nb_sentences=3),
            "education": [
                faker.sentence(),
                faker.sentence(),
            ],
            "experience": [
                {
                    "position": faker.job(),
                    "organization": faker.company(),
                    "years": f"{faker.year()}–{faker.year()}",
                }
            ],
        },
        "order": faker.unique.random_int(min=1, max=10_000),
        "is_visible": faker.boolean(),
    }

    return await directors_board_uow.director_board_member_repository.create(**creation_data)
