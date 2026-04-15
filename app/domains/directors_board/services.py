from typing import Annotated
from uuid import uuid4

from fastapi import Depends, UploadFile
from sqlalchemy import func, select, update

from app.core.config import s3_storage
from app.domains.directors_board.exceptions import DirectionBoardMemberNotFoundError
from app.domains.directors_board.infrastructure import (
    DirectorsBoardMemberUnitOfWork,
    get_director_board_member_unit_of_work,
)
from app.domains.directors_board.models import DirectorBoardMember
from app.domains.directors_board.schemas import BoardMemberSchema


class DirectorBoardMemberService:
    def __init__(self, uow):
        self.uow: DirectorsBoardMemberUnitOfWork = uow
        self.file_storage = s3_storage

    async def _get_member_or_fail(self, director_member_id: int) -> DirectorBoardMember:
        member = await self.uow.director_board_member_repository.get_first_by_kwargs(id=director_member_id)
        if not member:
            raise DirectionBoardMemberNotFoundError()
        return member

    async def get_all_directors(self) -> tuple[list[BoardMemberSchema], int]:
        async with self.uow:
            members, count = await self.uow.director_board_member_repository.list()
            schemas = []
            for member in members:
                schema = BoardMemberSchema.model_validate(member)
                if schema.photo_url:
                    schema.photo_url = await self.file_storage.get_presigned_object(schema.photo_url)
                schemas.append(schema)
            return schemas, count

    async def create_director_member(self, **kwargs) -> BoardMemberSchema:
        async with self.uow:
            max_order = (
                await self.uow._session.execute(select(func.coalesce(func.max(DirectorBoardMember.order), 0)))
            ).scalar_one_or_none()
            insert_data = {**kwargs, "order": max_order + 1}
            director = await self.uow.director_board_member_repository.create(**insert_data)
            return BoardMemberSchema.model_validate(director)

    async def update_director_member(self, director_member_id: int, data: dict) -> BoardMemberSchema:
        async with self.uow:
            updated_director_member = await self.uow.director_board_member_repository.update(director_member_id, **data)
            return BoardMemberSchema.model_validate(updated_director_member)

    async def delete_director_member(self, director_member_id: int) -> int:
        async with self.uow:
            member = await self._get_member_or_fail(director_member_id)
            if member.photo_url:
                await self.file_storage.delete_object(member.photo_url)
            return await self.uow.director_board_member_repository.mark_as_deleted(director_member_id)

    async def upload_photo(self, director_member_id: int, file: UploadFile) -> str:
        async with self.uow:
            await self._get_member_or_fail(director_member_id)

            ext = file.filename.split(".")[-1]
            filename = f"directors_board/{uuid4().hex}.{ext}"
            content = await file.read()
            await self.file_storage.upload_file(object_name=filename, file=content)
            
            await self.uow.director_board_member_repository.update(director_member_id, photo_url=filename)
            
            return filename

    async def delete_photo(self, director_member_id: int) -> None:
        async with self.uow:
            member = await self._get_member_or_fail(director_member_id)

            if member.photo_url:
                await self.file_storage.delete_object(member.photo_url)
                await self.uow.director_board_member_repository.update(director_member_id, photo_url=None)

    async def update_order(self, items):
        async with self.uow:
            # Temporary order for second card to exclude order duplication
            await self.uow._session.execute(
                update(DirectorBoardMember).where(DirectorBoardMember.id == items[1].id).values(order=9999)
            )

            for item in items:
                await self.uow._session.execute(
                    update(DirectorBoardMember).where(DirectorBoardMember.id == item.id).values(order=item.order)
                )
                await self.uow._session.commit()


def get_director_board_member_service(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
) -> DirectorBoardMemberService:
    return DirectorBoardMemberService(uow)


DirectorBoardMemberServiceDep = Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)]
