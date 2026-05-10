from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.payments.models import PaymentPurposeEnum


class PaymentsFilter(BaseModel):
    purpose: Annotated[PaymentPurposeEnum | None, Query(description="Purpose filter")] = None
    user_id: Annotated[int | None, Query(description="User ID filter")] = None
