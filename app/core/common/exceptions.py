class NotFoundError(Exception):
    """Raised when an entity/record was not found in DB"""


class NotResourceOwnerError(Exception):
    pass


class ResourceAlreadyExistsError(Exception):
    pass


class TimeCooldownError(Exception):
    pass


class InvalidOperationError(Exception):
    """Raised when an attempted operation is invalid in the current domain state."""

    pass
