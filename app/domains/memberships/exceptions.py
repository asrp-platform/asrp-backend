from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError


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
