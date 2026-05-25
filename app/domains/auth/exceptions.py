from app.core.common.exceptions import InvalidOperationError, ResourceAlreadyExistsError


class RegistrationAlreadyCompletedError(ResourceAlreadyExistsError):
    pass


class EmailAlreadyConfirmedError(ResourceAlreadyExistsError):
    pass


class EmailConfirmationExpiredError(InvalidOperationError):
    pass
