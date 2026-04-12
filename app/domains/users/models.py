from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from passlib.hash import bcrypt
from sqlalchemy import Boolean, DateTime, Enum as SQLAEnum, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base
from app.domains.memberships.models import MembershipRequest

if TYPE_CHECKING:
    from app.domains.feedback.models import FeedbackAdditionalInfo
    from app.domains.news.models import News
    from app.domains.payments.models import Payment
    from app.domains.permissions.models import Permission


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    firstname: Mapped[str] = mapped_column(nullable=False)
    middlename: Mapped[str] = mapped_column(nullable=True)
    lastname: Mapped[str] = mapped_column(nullable=False)
    preferred_name: Mapped[str | None] = mapped_column(nullable=True)
    suffix: Mapped[str] = mapped_column(nullable=True)
    credentials: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True, unique=True)
    stuff: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)
    country: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(nullable=True)
    city: Mapped[str] = mapped_column(nullable=False)
    languages_spoken: Mapped[str] = mapped_column(nullable=True)
    professional_interests: Mapped[str] = mapped_column(nullable=True)
    telegram_username: Mapped[str] = mapped_column(nullable=True, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
    pending: Mapped[bool] = mapped_column(default=True, nullable=True, server_default=text("true"))
    institution: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()

    last_password_change: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_name_change: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    email_confirmed: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    news: Mapped[list["News"]] = relationship("News", back_populates="author")
    membership_request: Mapped["MembershipRequest"] = relationship("MembershipRequest", back_populates="user")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", back_populates="users", secondary="users_permissions"
    )
    professional_information: Mapped["ProfessionalInformation"] = relationship(
        "ProfessionalInformation", back_populates="user", uselist=False
    )
    fellowships: Mapped[list["Fellowship"]] = relationship("Fellowship", back_populates="user")
    residencies: Mapped[list["Residency"]] = relationship("Residency", back_populates="user")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="user")
    name_change_requests: Mapped[list["NameChangeRequest"]] = relationship("NameChangeRequest", back_populates="user")
    communication_preferences: Mapped["CommunicationPreferences"] = relationship(
        "CommunicationPreferences", back_populates="user", uselist=False
    )
    feedback_additional_info: Mapped["FeedbackAdditionalInfo"] = relationship(
        "FeedbackAdditionalInfo", back_populates="user"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="user")

    _password: Mapped[str] = mapped_column()
    avatar_path: Mapped[str] = mapped_column(nullable=True, unique=True)

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = bcrypt.hash(value)

    def verify_password(self, plain_password: str) -> bool:
        return bcrypt.verify(plain_password, self._password)


class ProfessionalInformation(Base, UCIMixin):
    __tablename__ = "users_professional_information"

    medical_school: Mapped[str] = mapped_column(nullable=False)
    medical_school_country: Mapped[str] = mapped_column(nullable=False)
    years_from_to: Mapped[str] = mapped_column(nullable=False)

    is_board_certified_pathologist: Mapped[bool] = mapped_column(nullable=False, default=text("false"))
    is_us_pathology_trainee: Mapped[bool] = mapped_column(nullable=False, default=text("false"))
    is_us_lab_professional: Mapped[bool] = mapped_column(nullable=False, default=text("false"))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    user: Mapped["User"] = relationship("User", back_populates="professional_information")


class ProfessionalExperienceMixin:
    current_position: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    institution: Mapped[str] = mapped_column(nullable=False)
    speciality: Mapped[str] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(nullable=False)
    country: Mapped[str] = mapped_column(nullable=False)
    years_from_to: Mapped[str] = mapped_column(nullable=False)


class Residency(Base, UCIMixin, ProfessionalExperienceMixin):
    __tablename__ = "users_residency"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="residencies")


class Fellowship(Base, UCIMixin, ProfessionalExperienceMixin):
    __tablename__ = "users_fellowship"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="fellowships")


class Job(Base, UCIMixin, ProfessionalExperienceMixin):
    __tablename__ = "users_job"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="jobs")


class NameChangeRequestStatusEnum(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class NameChangeRequest(Base, UCIMixin):
    __tablename__ = "name_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    firstname: Mapped[str] = mapped_column(nullable=False)
    lastname: Mapped[str] = mapped_column(nullable=False)
    middlename: Mapped[str] = mapped_column(nullable=True)
    reason_change: Mapped[str] = mapped_column(nullable=False)
    reason_rejecting: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[NameChangeRequestStatusEnum] = mapped_column(
        SQLAEnum(NameChangeRequestStatusEnum, name="name_change_request_status_enum"),
        nullable=False,
        default=NameChangeRequestStatusEnum.PENDING,
        server_default=text("'PENDING'"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="name_change_requests")


class CommunicationPreferences(Base, UCIMixin):
    __tablename__ = "users_communication_preferences"

    membership_account_notifications: Mapped[bool] = mapped_column(
        Boolean(), default=True, nullable=False, server_default=text("true")
    )
    newsletters: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False, server_default=text("false"))
    events_meetings: Mapped[bool] = mapped_column(
        Boolean(), default=False, nullable=False, server_default=text("false")
    )
    committees_leadership: Mapped[bool] = mapped_column(
        Boolean(), default=False, nullable=False, server_default=text("false")
    )
    volunteer_opportunities: Mapped[bool] = mapped_column(
        Boolean(), default=False, nullable=False, server_default=text("false")
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    user: Mapped["User"] = relationship("User", back_populates="communication_preferences")
