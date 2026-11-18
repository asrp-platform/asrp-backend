from app.core.common.base_exceptions import (
    AuthenticationError,
    InvalidOperationError,
    PermissionDeniedError,
    ResourceConflictError,
)


# Login exceptions
class WrongCredentialsError(AuthenticationError):
    pass


class UserBannedError(PermissionDeniedError):
    pass


class UserDeletedError(AuthenticationError):
    pass


# Email confirmation exceptions
class EmailAlreadyConfirmedError(ResourceConflictError):
    pass


class EmailConfirmationExpiredError(AuthenticationError):
    pass


# Registration exceptions
class RegistrationAlreadyCompletedError(ResourceConflictError):
    pass


class EmailAlreadyInUseError(ResourceConflictError):
    pass


class InvalidPasswordResetTokenError(InvalidOperationError):
    pass


class InvalidCredentialsError(InvalidOperationError):
    pass
