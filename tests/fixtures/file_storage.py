from unittest.mock import patch

import pytest

from app.core.storage.storage_factory import get_file_storage

FileStorage = get_file_storage()

@pytest.fixture()
def spy_file_storage():
    with (
        patch.object(FileStorage, "upload_file", autospec=True, wraps=FileStorage.upload_file) as upload_file,
        patch.object(
            FileStorage,
            "get_file_url",
            autospec=True,
            wraps=FileStorage.get_file_url,
        ) as get_file_url,
        patch.object(
            FileStorage,
            "delete_file",
            autospec=True,
            wraps=FileStorage.delete_file,
        ) as delete_file,
    ):
        yield {
            "upload_file": upload_file,
            "get_file_url": get_file_url,
            "delete_file": delete_file,
        }
