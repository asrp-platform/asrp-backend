from unittest.mock import patch

import pytest

from app.core.storage.base_storage import S3BaseStorage


@pytest.fixture()
def spy_s3_storage():
    with (
        patch.object(S3BaseStorage, "upload_file", autospec=True, wraps=S3BaseStorage.upload_file) as upload_file,
        patch.object(
            S3BaseStorage,
            "get_presigned_object",
            autospec=True,
            wraps=S3BaseStorage.get_presigned_object,
        ) as get_presigned_object,
        patch.object(
            S3BaseStorage,
            "delete_object",
            autospec=True,
            wraps=S3BaseStorage.delete_object,
        ) as delete_object,
    ):
        yield {
            "upload_file": upload_file,
            "get_presigned_object": get_presigned_object,
            "delete_object": delete_object,
        }
