from app.core.common.exceptions import NotFoundError, AlreadyExistsResourceError, TimeCooldownError


class InvalidPasswordError(Exception):
    pass


class ResidencyNotFoundError(NotFoundError):
    pass


class UserNotFoundError(NotFoundError):
    pass


class FellowshipNotFoundError(NotFoundError):
    pass


class UsernameChangeNotFoundError(NotFoundError):
    pass


class ActiveUsernameChangeAlreadyExistsError(AlreadyExistsResourceError):
    pass


class UsernameChangeCooldownNotExpiredError(TimeCooldownError):
    pass
