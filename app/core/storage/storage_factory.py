from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import InvalidStorageTypeError
from app.core.config import FileStorageTypeEnum, settings
from app.core.storage.base_storage import BaseFileStorage
from app.core.storage.s3_storage import S3Storage


@lru_cache
def get_file_storage() -> BaseFileStorage:
    if settings.FILE_STORAGE_TYPE == FileStorageTypeEnum.S3_STORAGE:
        return S3Storage(
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            endpoint_url=settings.s3_endpoint_url,
            default_bucket_name=settings.S3_DEFAULT_BUCKET,
            region_name=settings.S3_REGION,
            public_url=settings.s3_public_url,
            expires_in=settings.FILE_STORAGE_URL_EXPIRES_IN,
)
    else:
        raise InvalidStorageTypeError("Unknown storage type")


FileStorageDep = Annotated[BaseFileStorage, Depends(get_file_storage)]