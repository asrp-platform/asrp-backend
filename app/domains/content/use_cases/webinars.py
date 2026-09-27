from typing import Annotated, Any

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.content.services import WebinarServiceDep


class GetWebinarsUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(
        self, *, user_id: int | None, limit: int, offset: int, order_by: str | None, filters: dict[str, Any]
    ):
        return await self.__service.get_user_webinars_paginated_counted(
            user_id=user_id, order_by=order_by, filters=filters, limit=limit, offset=offset
        )


class RegisterForWebinarUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(self, webinar_slug: str, user_id: int) -> None:
        await self.__service.register_for_webinar(webinar_slug, user_id)


class GetWebinarPlaybackUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(self, webinar_slug: str, user_id: int) -> str | None:
        return await self.__service.generate_webinar_embed_url(webinar_slug, user_id)


class GetAdminWebinarsUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(
        self, permissions: list[str], *, limit: int, offset: int, order_by: str | None, filters: dict[str, Any]
    ):
        check_permissions("webinars.view", permissions)
        return await self.__service.get_all_paginated_counted(
            order_by=order_by, filters=filters, limit=limit, offset=offset, open_transaction=True
        )


class CreateWebinarUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(self, permissions: list[str], data: dict[str, Any]):
        check_permissions("webinars.create", permissions)
        return await self.__service.create_webinar(open_transaction=True, **data)


class GetWebinarUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(self, permissions: list[str], webinar_id: int):
        check_permissions("webinars.view", permissions)
        return await self.__service.get_webinar_by_id(webinar_id)


class UpdateWebinarUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(self, permissions: list[str], webinar_id: int, data: dict[str, Any]):
        check_permissions("webinars.update", permissions)
        return await self.__service.update_webinar(webinar_id, open_transaction=True, **data)


class DeleteWebinarUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(self, permissions: list[str], webinar_id: int):
        check_permissions("webinars.delete", permissions)
        return await self.__service.delete_webinar(webinar_id, open_transaction=True)


class GetRegisteredWebinarUsersUseCase:
    def __init__(self, service: WebinarServiceDep):
        self.__service = service

    async def execute(self, permissions: list[str], webinar_id: int, *, limit: int, offset: int, order_by: str | None):
        check_permissions("webinars.view", permissions)
        return await self.__service.get_registered_users_paginated_counted(
            webinar_id, limit=limit, offset=offset, order_by=order_by
        )


GetWebinarsUseCaseDep = Annotated[GetWebinarsUseCase, Depends(GetWebinarsUseCase)]
RegisterForWebinarUseCaseDep = Annotated[RegisterForWebinarUseCase, Depends(RegisterForWebinarUseCase)]
GetWebinarPlaybackUseCaseDep = Annotated[GetWebinarPlaybackUseCase, Depends(GetWebinarPlaybackUseCase)]
GetAdminWebinarsUseCaseDep = Annotated[GetAdminWebinarsUseCase, Depends(GetAdminWebinarsUseCase)]
CreateWebinarUseCaseDep = Annotated[CreateWebinarUseCase, Depends(CreateWebinarUseCase)]
GetWebinarUseCaseDep = Annotated[GetWebinarUseCase, Depends(GetWebinarUseCase)]
UpdateWebinarUseCaseDep = Annotated[UpdateWebinarUseCase, Depends(UpdateWebinarUseCase)]
DeleteWebinarUseCaseDep = Annotated[DeleteWebinarUseCase, Depends(DeleteWebinarUseCase)]
GetRegisteredWebinarUsersUseCaseDep = Annotated[
    GetRegisteredWebinarUsersUseCase, Depends(GetRegisteredWebinarUsersUseCase)
]
