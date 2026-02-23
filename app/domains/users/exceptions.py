from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError, TimeCooldownError


class InvalidPasswordError(Exception):
    pass


class ResidencyNotFoundError(NotFoundError):
    pass


class UserNotFoundError(NotFoundError):
    pass


class FellowshipNotFoundError(NotFoundError):
    pass


class NameChangeRequestNotFoundError(NotFoundError):
    pass


class PendingNameChangeRequestAlreadyExistsError(ResourceAlreadyExistsError):
    pass


class NameChangeRequestCooldownNotExpiredError(TimeCooldownError):
    pass
