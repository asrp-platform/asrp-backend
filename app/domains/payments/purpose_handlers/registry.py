from typing import Annotated

from fastapi import Depends

from app.domains.payments.models import PaymentPurposeEnum
from app.domains.payments.purpose_handlers.membership_application import MembershipApplicationHandlerDep


class PaymentPurposeHandlerRegistry:
    def __init__(
        self,
        membership_application_handler: MembershipApplicationHandlerDep,
    ):
        self.__handlers = {
            PaymentPurposeEnum.MEMBERSHIP_APPLICATION: membership_application_handler,
        }

    def get(self, purpose: PaymentPurposeEnum):
        return self.__handlers[purpose]


PaymentPurposeHandlerRegistryDep = Annotated[PaymentPurposeHandlerRegistry, Depends(PaymentPurposeHandlerRegistry)]
