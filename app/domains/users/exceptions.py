from app.core.common.exceptions import (
    InvalidOperationError,
    ResourceAlreadyExistsError,
    TimeCooldownError,
)


class InvalidPasswordError(Exception):
    pass


class ProfessionalExperienceCurrentPositionExistsError(ResourceAlreadyExistsError):
    pass


class PendingNameChangeRequestAlreadyExistsError(ResourceAlreadyExistsError):
    pass


class NameChangeRequestCooldownNotExpiredError(TimeCooldownError):
    pass


class CannotDeleteLastResidencyError(InvalidOperationError):
    pass


class GrantAdminRoleForbiddenError(Exception):
    pass


class RevokeAdminRoleForbiddenError(Exception):
    pass
