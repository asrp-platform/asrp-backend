class NotFoundError(Exception):
    pass


class NotResourceOwnerError(Exception):
    pass


class ResourceAlreadyExistsError(Exception):
    pass


class TimeCooldownError(Exception):
    pass
