from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.core.common.exceptions import NotFoundError, PermissionDeniedError
from app.core.config import settings
from app.core.utils.permissions import check_permissions
from app.domains.content.filters import WebinarStartFilterEnum
from app.domains.content.models import Webinar, WebinarRegisteredUsers
from app.domains.memberships.utils import has_member_access
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetWebinarsUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(
        self, *, user_id: int | None, limit: int, offset: int, order_by: str | None, filters: dict[str, Any]
    ):
        async with self.__tm:
            membership = None
            if user_id is not None:
                membership = await self.__tm.user_membership_repository.get_first_by_kwargs(user_id=user_id)
            stmt = select(Webinar).options(selectinload(Webinar.registered_users)) if user_id is not None else None
            webinars, count = await self.__tm.webinar_repository.list(
                limit, offset, order_by, _apply_start_filter(filters), stmt=stmt
            )
            return webinars, count, membership


class RegisterForWebinarUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, webinar_slug: str, user_id: int) -> None:
        async with self.__tm:
            webinar = await self.__tm.webinar_repository.get_first_by_kwargs(slug=webinar_slug)
            if webinar is None:
                raise NotFoundError("Webinar with provided slug not found")

            user = await self.__tm.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise NotFoundError("User with provided ID not found")
            if not webinar.member_only:
                raise PermissionDeniedError("Public webinars use external registration")

            membership = await self.__tm.user_membership_repository.get_first_by_kwargs(user_id=user_id)
            if not has_member_access(membership):
                raise PermissionDeniedError("Active membership is required to register for this webinar")

            statement = (
                insert(WebinarRegisteredUsers)
                .values(webinar_id=webinar.id, user_id=user.id)
                .on_conflict_do_nothing(index_elements=["webinar_id", "user_id"])
            )
            await self.__tm.execute(statement)


class GetWebinarPlaybackUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, webinar_slug: str, user_id: int) -> str | None:
        async with self.__tm:
            webinar = await self.__tm.webinar_repository.get_first_by_kwargs(slug=webinar_slug)
            if webinar is None:
                raise NotFoundError("Webinar with provided slug not found")

            membership = await self.__tm.user_membership_repository.get_first_by_kwargs(user_id=user_id)
            if not has_member_access(membership):
                raise PermissionDeniedError("Active membership is required to view this webinar")

            if webinar.bunny_video_id is None:
                return None

            return _generate_bunny_embed_url(webinar.bunny_video_id)


def _generate_bunny_embed_url(video_id: str, expires_in: int = 60 * 60) -> str:
    import hashlib
    import time

    expires = int(time.time()) + expires_in
    raw_token = f"{settings.BUNNY_STREAM_TOKEN_KEY}{video_id}{expires}"
    token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return (
        f"https://iframe.mediadelivery.net/embed/{settings.BUNNY_LIBRARY_ID}/{video_id}?token={token}&expires={expires}"
    )


class GetAdminWebinarsUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(
        self, permissions: list[str], *, limit: int, offset: int, order_by: str | None, filters: dict[str, Any]
    ):
        check_permissions("webinars.view", permissions)
        async with self.__tm:
            return await self.__tm.webinar_repository.list(limit, offset, order_by, _apply_start_filter(filters))


class CreateWebinarUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, permissions: list[str], data: dict[str, Any]):
        check_permissions("webinars.create", permissions)
        async with self.__tm:
            return await self.__tm.webinar_repository.create(**data)


class GetWebinarUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, permissions: list[str], webinar_id: int):
        check_permissions("webinars.view", permissions)
        async with self.__tm:
            webinar = await self.__tm.webinar_repository.get_first_by_kwargs(id=webinar_id)
            if webinar is None:
                raise NotFoundError("Webinar with provided ID not found")
            return webinar


class UpdateWebinarUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, permissions: list[str], webinar_id: int, data: dict[str, Any]):
        check_permissions("webinars.update", permissions)
        if starts_at := data.get("starts_at"):
            from datetime import timedelta

            data["ends_at"] = starts_at + timedelta(hours=2)
        async with self.__tm:
            return await self.__tm.webinar_repository.update(webinar_id, **data)


class DeleteWebinarUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, permissions: list[str], webinar_id: int):
        check_permissions("webinars.delete", permissions)
        async with self.__tm:
            return await self.__tm.webinar_repository.mark_as_deleted(webinar_id)


class GetRegisteredWebinarUsersUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.__tm = transaction_manager

    async def execute(self, permissions: list[str], webinar_id: int, *, limit: int, offset: int, order_by: str | None):
        check_permissions("webinars.view", permissions)
        async with self.__tm:
            webinar = await self.__tm.webinar_repository.get_first_by_kwargs(id=webinar_id)
            if webinar is None:
                raise NotFoundError("Webinar with provided ID not found")
            return await self.__tm.webinar_repository.list_registered_users(
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


def _apply_start_filter(filters: dict[str, Any] | None) -> dict[str, Any]:
    filters = (filters or {}).copy()
    status = filters.pop("status", WebinarStartFilterEnum.ALL)
    now = datetime.now(timezone.utc)
    if status == WebinarStartFilterEnum.UPCOMING:
        filters["ends_at__gte"] = now
    elif status == WebinarStartFilterEnum.PAST:
        filters["ends_at__lte"] = now
    return filters
