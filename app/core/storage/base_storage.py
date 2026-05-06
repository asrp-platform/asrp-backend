from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class UploadedFileData:
    object_key: str
    metadata: dict[str, Any] | None = None


class BaseFileStorage(ABC):
    """
    S3 implementation methods supports kwargs:
        - bucket_name: str (overrides default)
    """

    def __init__(self, *, expires_in: int):
        """:param expires_in: seconds until expiration"""
        self.expires_in = expires_in

    @abstractmethod
    async def get_file_url(
            self,
            object_key: str,
            expires_in: int | None = None,
            **kwargs
    ) -> str | None:
        """:param expires_in: seconds until expiration"""
        pass

    @abstractmethod
    async def upload_file(self, object_key: str, file_content: bytes, **kwargs) -> UploadedFileData:
        pass

    @abstractmethod
    async def delete_file(self, object_key: str, **kwargs) -> None:
        pass

    @abstractmethod
    async def check_file_exists(self, object_key: str, **kwargs) -> bool:
        pass
