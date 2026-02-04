import shutil
from io import BytesIO
from pathlib import Path

import pytest
from faker import Faker
from fastapi import UploadFile

from app.core.config import BASE_DIR
from app.core.utils.save_file import save_file

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="function")
def temp_media_dir():
    """Fixture to create and cleanup a temporary media directory for tests."""
    test_dir = Path("tests_media")
    full_path = BASE_DIR / test_dir
    full_path.mkdir(parents=True, exist_ok=True)
    yield test_dir
    if full_path.exists():
        shutil.rmtree(full_path)


async def test_save_file_auto_filename(temp_media_dir, faker: Faker):
    content = faker.binary(length=12)
    filename = faker.file_name(extension="txt")
    file = UploadFile(file=BytesIO(content), filename=filename)

    saved_path = await save_file(file, temp_media_dir)

    full_saved_path = BASE_DIR / saved_path
    assert full_saved_path.exists()
    assert full_saved_path.suffix == ".txt"
    assert full_saved_path.name != filename  # Should be a uuid
    with open(full_saved_path, "rb") as f:
        assert f.read() == content


async def test_save_file_explicit_filename(temp_media_dir, faker: Faker):
    content = faker.binary(length=12)
    explicit_name = faker.file_name(extension="pdf")
    file = UploadFile(file=BytesIO(content), filename=faker.file_name(extension="pdf"))

    saved_path = await save_file(file, temp_media_dir, filename=explicit_name)

    full_saved_path = BASE_DIR / saved_path
    assert full_saved_path.exists()
    assert full_saved_path.name == explicit_name
    with open(full_saved_path, "rb") as f:
        assert f.read() == content


