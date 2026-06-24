from datetime import date
from typing import Annotated, Sequence

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.feedback.models import FeedbackAdditionalInfo
from app.domains.feedback.services import FeedbackAdditionalInfoServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetInterestsUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        feedback_service: FeedbackAdditionalInfoServiceDep,
    ):
        self.__tm = transaction_manager
        self.__feedback_service = feedback_service

    async def execute(
        self,
        permissions: list[str],
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        has_telegram: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[Sequence[FeedbackAdditionalInfo], int]:
        check_permissions("feedback.view", permissions)

        data, count = await self.__feedback_service.get_interests_paginated_counted(
            limit=limit,
            offset=offset,
            search=search,
            has_telegram=has_telegram,
            date_from=date_from,
            date_to=date_to,
        )

        return data, count


GetInterestsUseCaseDep = Annotated[GetInterestsUseCase, Depends(GetInterestsUseCase)]
