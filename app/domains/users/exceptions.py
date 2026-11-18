from app.core.common.base_exceptions import (
    InvalidOperationError,
    PermissionDeniedError,
    ResourceConflictError,
)


class WrongPasswordError(PermissionDeniedError):
    pass


class ProfessionalExperienceCurrentPositionExistsError(ResourceConflictError):
    pass


class PendingNameChangeRequestAlreadyExistsError(ResourceConflictError):
    pass


class LastResidencyRemovalError(InvalidOperationError):
    pass


class NameChangeRequestCooldownNotExpiredError(Exception):
    pass
