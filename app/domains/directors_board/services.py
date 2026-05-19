from typing import Annotated
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from fastapi import Depends
from loguru import logger
from sqlalchemy import func, select, update

from app.core.common.exceptions import InvalidMimeTypeError
from app.core.config import settings
from app.core.storage.base_storage import BaseFileStorage
from app.core.storage.storage_factory import FileStorageDep
from app.domains.directors_board.exceptions import DirectionBoardMemberNotFoundError
from app.domains.directors_board.models import DirectorBoardMember
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData


class DirectorsBoardService:
    def __init__(self, transaction_manager, file_storage: BaseFileStorage):
        self.transaction_manager = transaction_manager
        self.file_storage = file_storage
        self.bucket_name = settings.S3_DEFAULT_BUCKET

    async def get_directors_board_members(self):
        members, count = await self.transaction_manager.directors_board_member_repository.list()

        for member in members:
            if member.photo_url:
                member.photo_url = await self.get_photo_url_by_object_key(member.photo_url)

        return members, count

    async def create_director_member(self, **kwargs):
        max_order = (
            await self.transaction_manager._session.execute(
                select(func.coalesce(func.max(DirectorBoardMember.order), 0))
            )
        ).scalar_one_or_none()
        insert_data = {
            **kwargs,
            "photo_url": self._extract_object_key(kwargs.get("photo_url")),
            "order": max_order + 1,
        }
        return await self.transaction_manager.directors_board_member_repository.create(**insert_data)

    async def update_director_member(self, director_member_id: int, **kwargs):
        if "photo_url" in kwargs:
            kwargs["photo_url"] = self._extract_object_key(kwargs.get("photo_url"))
        return await self.transaction_manager.directors_board_member_repository.update(director_member_id, **kwargs)

    async def delete_director_member(self, director_member_id: int) -> int:
        return await self.transaction_manager.directors_board_member_repository.mark_as_deleted(director_member_id)

    async def update_order(self, items):
        # Temporary order for second card to exclude order duplication
        await self.transaction_manager._session.execute(
            update(DirectorBoardMember).where(DirectorBoardMember.id == items[1].id).values(order=9999)
        )

        for item in items:
            await self.transaction_manager._session.execute(
                update(DirectorBoardMember).where(DirectorBoardMember.id == item.id).values(order=item.order)
            )
            await self.transaction_manager._session.commit()

    async def upload_photo(self, director_member_id: int, file_data: FileData) -> str:
        if not file_data.content_type.startswith("image/"):
            raise InvalidMimeTypeError("Invalid image content type")

        async with self.transaction_manager:
            director_member = await self.transaction_manager.directors_board_member_repository.get_first_by_kwargs(
                id=director_member_id
            )
        if director_member is None:
            raise DirectionBoardMemberNotFoundError("DirectionBoardMember with provided id not found")

        old_filename = director_member.photo_url
        new_filename = f"directors_board/{uuid4()}.{file_data.filename.split('.')[-1]}"

        upload_result = await self.file_storage.upload_file(
            new_filename,
            file_data.content
        )


        try:
            async with self.transaction_manager:
                await self.transaction_manager.directors_board_member_repository.update(
                    director_member_id, photo_url=new_filename
                )
        except Exception:
            await self.file_storage.delete_file(new_filename)

        try:
            if old_filename is not None:
                await self.file_storage.delete_file(old_filename)
        except Exception:
            logger.exception(f"Failed to delete file {old_filename}")

        return upload_result.object_key

    async def get_photo_url_by_object_key(self, object_key: str) -> str:
        normalized_object_key = self._extract_object_key(object_key)
        if normalized_object_key is None:
            return object_key
        return await self.file_storage.get_file_url(normalized_object_key)

    def _extract_object_key(self, stored_value: str | None) -> str | None:
        if stored_value is None:
            return None

        if "://" not in stored_value:
            return stored_value.lstrip("/")

        parsed = urlsplit(stored_value)
        path = unquote(parsed.path.lstrip("/"))
        bucket_prefix = f"{self.bucket_name}/"

        if path.startswith(bucket_prefix):
            return path[len(bucket_prefix) :]

        if path.startswith("directors_board/"):
            return path

        return None


def get_director_board_member_service(
    transaction_manager: TransactionManagerDep,
    file_storage: FileStorageDep,
) -> DirectorsBoardService:
    return DirectorsBoardService(transaction_manager, file_storage)


DirectorBoardMemberServiceDep = Annotated[DirectorsBoardService, Depends(get_director_board_member_service)]
