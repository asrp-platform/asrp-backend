from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError


class MembershipRequestNotFoundError(NotFoundError):
    pass


class MembershipNotActiveError(Exception):
    pass


class MembershipAccessDeniedError(Exception):
    pass


class MembershipTypeNotFoundError(NotFoundError):
    pass


class MembershipRequestAlreadyExistsError(ResourceAlreadyExistsError):
    pass
