from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetCaseTagsUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self):
        async with self.__tm:
            tags, _ = await self.__tm.case_tag_repository.list(order_by="name")
            return tags


class GetCaseTagUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, tag_id: int):
        async with self.__tm:
            tag = await self.__tm.case_tag_repository.get_first_by_kwargs(id=tag_id)
            if tag is None:
                raise NotFoundError("Case tag with provided ID not found")
            return tag


class CreateCaseTagUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, name: str):
        async with self.__tm:
            existing_tag = await self.__tm.case_tag_repository.get_first_by_kwargs(name=name)
            if existing_tag is not None:
                raise ResourceAlreadyExistsError("Case tag with provided name already exists")
            return await self.__tm.case_tag_repository.create(name=name)


class UpdateCaseTagUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, tag_id: int, data: dict):
        async with self.__tm:
            tag = await self.__tm.case_tag_repository.get_first_by_kwargs(id=tag_id)
            if tag is None:
                raise NotFoundError("Case tag with provided ID not found")

            if name := data.get("name"):
                existing_tag = await self.__tm.case_tag_repository.get_first_by_kwargs(name=name)
                if existing_tag is not None and existing_tag.id != tag_id:
                    raise ResourceAlreadyExistsError("Case tag with provided name already exists")

            return await self.__tm.case_tag_repository.update(tag_id, **data)


class DeleteCaseTagUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, tag_id: int) -> None:
        async with self.__tm:
            tag = await self.__tm.case_tag_repository.get_first_by_kwargs(id=tag_id)
            if tag is None:
                raise NotFoundError("Case tag with provided ID not found")

            if await self.__tm.case_tag_repository.has_active_cases(tag_id):
                raise ResourceAlreadyExistsError("Case tag cannot be deleted because it is used by cases")

            await self.__tm.case_tag_repository.mark_as_deleted(tag_id)


GetCaseTagsUseCaseDep = Annotated[GetCaseTagsUseCase, Depends(GetCaseTagsUseCase)]
GetCaseTagUseCaseDep = Annotated[GetCaseTagUseCase, Depends(GetCaseTagUseCase)]
CreateCaseTagUseCaseDep = Annotated[CreateCaseTagUseCase, Depends(CreateCaseTagUseCase)]
UpdateCaseTagUseCaseDep = Annotated[UpdateCaseTagUseCase, Depends(UpdateCaseTagUseCase)]
DeleteCaseTagUseCaseDep = Annotated[DeleteCaseTagUseCase, Depends(DeleteCaseTagUseCase)]
