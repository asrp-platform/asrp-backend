from app.core.common.exceptions import NotFoundError


class MembershipNotFoundError(NotFoundError):
    pass


class MembershipNotActiveError(Exception):
    pass


class MembershipAccessDeniedError(Exception):
    pass


class MembershipTypeNotFoundError(NotFoundError):
    pass
