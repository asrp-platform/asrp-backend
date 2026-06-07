from datetime import date
from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.feedback.schemas import FeedbackInterestResponseSchema
from app.domains.feedback.services import FeedbackAdditionalInfoService, FeedbackAdditionalInfoServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetInterestsUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        feedback_service: FeedbackAdditionalInfoService,
    ):
        self.__transaction_manager = transaction_manager
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
    ) -> tuple[list[FeedbackInterestResponseSchema], int]:
        check_permissions("feedback.view", permissions)

        data, count = await self.__feedback_service.get_interests_paginated_counted(
            limit=limit,
            offset=offset,
            search=search,
            has_telegram=has_telegram,
            date_from=date_from,
            date_to=date_to,
        )

        schema_data = [FeedbackInterestResponseSchema.model_validate(item) for item in data]
        return schema_data, count


def get_use_case(
    transaction_manager: TransactionManagerDep,
    feedback_service: FeedbackAdditionalInfoServiceDep,
) -> GetInterestsUseCase:
    return GetInterestsUseCase(transaction_manager, feedback_service)


GetInterestsUseCaseDep = Annotated[GetInterestsUseCase, Depends(get_use_case)]
