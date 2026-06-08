from stripe import Event

from app.domains.memberships.services import MembershipRequestServiceDep
from app.domains.payments.models import Payment
from app.domains.payments.services import PaymentServiceDep


class MembershipRenewalHandler:
    def __init__(
        self,
        membership_service: MembershipRequestServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self.__membership_service = membership_service
        self.__payment_service = payment_service

    async def on_succeeded(self, payment: Payment, event: Event) -> None:
        pass

    async def on_failed(self, payment: Payment, event: Event) -> None:
        pass

    async def on_expired(self, payment: Payment, event: Event) -> None:
        pass

    async def on_checkout_session_completed(self, payment, event: Event) -> None:
        pass
