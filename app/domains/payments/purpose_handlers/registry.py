from typing import Annotated

from fastapi import Depends
from loguru import logger

from app.core.common.exceptions import HandlerNotFoundError
from app.domains.payments.models import PaymentPurposeEnum
from app.domains.payments.purpose_handlers.membership_application import MembershipApplicationHandlerDep
from app.domains.payments.purpose_handlers.membership_renewal import MembershipRenewalHandlerDep


class PaymentPurposeHandlerRegistry:
    def __init__(
        self,
        membership_application_handler: MembershipApplicationHandlerDep,
        membership_renewal_handler: MembershipRenewalHandlerDep,
    ):
        self.__handlers = {
            PaymentPurposeEnum.MEMBERSHIP_APPLICATION: membership_application_handler,
            PaymentPurposeEnum.MEMBERSHIP_RENEWAL: membership_renewal_handler,
        }

    def get(self, purpose: PaymentPurposeEnum):
        handler = self.__handlers.get(purpose)
        if handler is None:
            logger.error("Payment purpose handler not found: purpose={}", purpose)
            raise HandlerNotFoundError(f"Payment purpose handler not found for purpose={purpose}")
        return handler


PaymentPurposeHandlerRegistryDep = Annotated[PaymentPurposeHandlerRegistry, Depends(PaymentPurposeHandlerRegistry)]
