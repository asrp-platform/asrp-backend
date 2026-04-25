from typing import Annotated
from urllib.parse import unquote, urlsplit

from fastapi import Depends
from sqlalchemy import func, select, update

from app.core.config import s3_storage, settings
from app.domains.directors_board.models import DirectorBoardMember
from app.domains.shared.transaction_managers import TransactionManagerDep


class DirectorsBoardService:
    def __init__(self, transaction_manager):
        self.transaction_manager = transaction_manager
        self.file_storage = s3_storage
        self.bucket_name = settings.S3_DEFAULT_BUCKET

    async def get_directors_board_members(self):
        return await self.transaction_manager.directors_board_member_repository.list()

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

    async def hydrate_photo_urls(self, members: list[DirectorBoardMember]) -> None:
        for member in members:
            member.photo_url = await self._get_fresh_photo_url(member.photo_url)

    async def hydrate_photo_url(self, member: DirectorBoardMember) -> DirectorBoardMember:
        member.photo_url = await self._get_fresh_photo_url(member.photo_url)
        return member

    async def _get_fresh_photo_url(self, stored_value: str | None) -> str | None:
        object_key = self._extract_object_key(stored_value)
        if object_key is None:
            return None
        return await self.file_storage.get_presigned_object(object_key)

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


def get_director_board_member_service(transaction_manager: TransactionManagerDep) -> DirectorsBoardService:
    return DirectorsBoardService(transaction_manager)


DirectorBoardMemberServiceDep = Annotated[DirectorsBoardService, Depends(get_director_board_member_service)]
