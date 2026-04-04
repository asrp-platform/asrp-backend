from app.core.common.exceptions import (
    InvalidOperationError,
    NotFoundError,
    ResourceAlreadyExistsError,
    TimeCooldownError,
)


class InvalidPasswordError(Exception):
    pass


class ResidencyNotFoundError(NotFoundError):
    pass


class UserNotFoundError(NotFoundError):
    pass


class FellowshipNotFoundError(NotFoundError):
    pass


class JobNotFoundError(NotFoundError):
    pass


class ProfessionalExperienceCurrentPositionExistsError(ResourceAlreadyExistsError):
    pass


class NameChangeRequestNotFoundError(NotFoundError):
    pass


class PendingNameChangeRequestAlreadyExistsError(ResourceAlreadyExistsError):
    pass


class NameChangeRequestCooldownNotExpiredError(TimeCooldownError):
    pass


class CannotDeleteLastResidencyError(InvalidOperationError):
    pass
