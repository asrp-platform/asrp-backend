# STATUS BASE EXCEPTIONS - catching in main.py

# Handler - 400
class BadRequestError(Exception):
    pass


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


# 415 Handler
class InvalidMimeTypeError(Exception):
    pass


# Handler - 413
class PayloadTooLargeError(Exception):
    pass


# BASE OPERATIONS EXCEPTION
class InvalidStorageTypeError(Exception):
    pass


class HandlerNotFoundError(Exception):
    pass


class RequestParamsError(BadRequestError):
    pass


class InvalidOperationError(BadRequestError):
    """Raised when an attempted operation is invalid in the current domain state."""

    pass
