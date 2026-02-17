from app.core.common.exceptions import NotFoundError


class InvalidPasswordError(Exception):
    pass


class ResidencyNotFoundError(NotFoundError):
    pass


class UserNotFoundError(NotFoundError):
    pass


class FellowshipNotFoundError(NotFoundError):
    pass
