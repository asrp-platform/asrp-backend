from typing import Any

import pytest
from faker import Faker

from app.domains.shared.transaction_managers import TransactionManager
from app.domains.emails.models import EmailTemplate


@pytest.fixture(scope="function")
async def email_template_data(faker: Faker) -> dict[str, Any]:
    return {
        "name": faker.name(),
        "subject": faker.pystr(),
        "description": faker.pystr(),
        "editor_state": {
            "blocks": [],
            "version": "1.6.1"
        },
        "html": faker.pystr(),
    }


@pytest.fixture(scope="function")
async def email_template_db(
    test_transaction_manager: TransactionManager,
    email_template_data: dict[str, Any],
) -> EmailTemplate:
    async with test_transaction_manager:
        return await test_transaction_manager.email_templates_repository.create(**email_template_data)
