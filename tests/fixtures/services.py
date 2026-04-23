import pytest

from app.domains.feedback.services import FeedbackAdditionalInfoService
from app.domains.memberships.services import MembershipService
from app.domains.payments.services import PaymentService
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.services import CommunicationPreferencesService


@pytest.fixture()
def membership_service(test_transaction_manager: TransactionManager):
    return MembershipService(test_transaction_manager)


@pytest.fixture()
def feedback_additional_info_service(test_transaction_manager: TransactionManager):
    return FeedbackAdditionalInfoService(test_transaction_manager)


@pytest.fixture()
def communication_preference_service(test_transaction_manager: TransactionManager):
    return CommunicationPreferencesService(test_transaction_manager)


@pytest.fixture()
def payment_service(test_transaction_manager: TransactionManager):
    return PaymentService(test_transaction_manager)
