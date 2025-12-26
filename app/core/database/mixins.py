from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class UCIMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )


class UCIMixinSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
