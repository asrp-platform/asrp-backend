class NotFoundError(Exception):
    pass


class NotResourceOwnerError(Exception):
    pass


class AlreadyExistsResourceError(Exception):
    pass


class TimeCooldownError(Exception):
    pass
