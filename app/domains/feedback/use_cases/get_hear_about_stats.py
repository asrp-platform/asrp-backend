from datetime import date
from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.feedback.constants import HEAR_ABOUT_ASRP_OPTIONS
from app.domains.feedback.schemas import HearAboutOptionStatsSchema, HearAboutStatsResponseSchema
from app.domains.feedback.services import FeedbackAdditionalInfoServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetHearAboutStatsUseCase:
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
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> HearAboutStatsResponseSchema:
        check_permissions("feedback.view", permissions)

        raw_stats = await self.__feedback_service.get_hear_about_stats(
            date_from=date_from,
            date_to=date_to,
        )

        # Keep stats aligned with Select options and fold unknown legacy values into "other".
        stats_dict = {opt: 0 for opt in HEAR_ABOUT_ASRP_OPTIONS}
        fallback_option = "other"
        for item in raw_stats:
            option = item["option"]
            count = item["count"]
            if option in stats_dict:
                stats_dict[option] += count
            else:
                stats_dict[fallback_option] += count

        total_responses = sum(stats_dict.values())

        option_stats = []
        for option, count in stats_dict.items():
            percentage = 0.0
            if total_responses > 0:
                percentage = round((count / total_responses) * 100, 2)
            option_stats.append(
                HearAboutOptionStatsSchema(
                    option=option,
                    count=count,
                    percentage=percentage,
                )
            )

        # Order option_stats descending by count, then alphabetically by option name
        option_stats.sort(key=lambda x: (-x.count, x.option))

        return HearAboutStatsResponseSchema(
            total_responses=total_responses,
            stats=option_stats,
        )


GetHearAboutStatsUseCaseDep = Annotated[GetHearAboutStatsUseCase, Depends(GetHearAboutStatsUseCase)]
