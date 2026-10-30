# Handled - 404
class NotFoundError(Exception):
    """Raised when an entity/record was not found in DB"""


# Handled - 401
class AuthenticationError(Exception):
    """401 status code - wrong credentials == unauthorized"""


# Handled - 403
class PermissionDeniedError(Exception):
    pass


# Handled - 409
class ResourceConflictError(Exception):
    pass


class InvalidOperationError(Exception):
    """Raised when an attempted operation is invalid in the current domain state."""

    pass


class InvalidMimeTypeError(Exception):
    pass


class PayloadTooLargeError(Exception):
    pass


class InvalidStorageTypeError(Exception):
    pass


class HandlerNotFoundError(Exception):
    pass
