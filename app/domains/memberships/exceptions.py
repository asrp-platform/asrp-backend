from app.core.common.exceptions import ResourceAlreadyExistsError, NotFoundError


class MembershipNotFoundError(NotFoundError):
    pass


class MembershipNotActiveError(Exception):
    pass


class MembershipAccessDeniedError(Exception):
    pass


class MembershipTypeNotFoundError(NotFoundError):
    pass


class MembershipAlreadyExistsError(ResourceAlreadyExistsError):
    pass
