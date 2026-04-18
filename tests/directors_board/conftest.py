from typing import Any

import pytest
from faker import Faker

from app.domains.directors_board.models import DirectorBoardMember
from app.domains.shared.transaction_managers import TransactionManager


@pytest.fixture(scope="function")
async def directors_board_member_data(faker: Faker) -> dict[str, Any]:
    return {
        "role": faker.pystr(),
        "name": faker.name(),
        "content": faker.pydict(),
    }


@pytest.fixture(scope="function")
async def directors_board_member_db(
    faker: Faker,
    test_transaction_manager: TransactionManager,
    directors_board_member_data: dict[str, Any],
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

    return await test_transaction_manager.directors_board_member_repository.create(**creation_data)
