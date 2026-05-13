from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError


class MembershipNotActiveError(Exception):
    pass


class MembershipAccessDeniedError(Exception):
    pass


class MembershipTypeNotFoundError(NotFoundError):
    pass


class MembershipRequestAlreadyExistsError(ResourceAlreadyExistsError):
    pass


class MembershipAlreadyPaidError(Exception):
    pass


class MembershipRequestCannotBeReappliedError(Exception):
    pass


class MembershipApplicationCheckoutError(Exception):
    pass


class MissingRejectingCommentError(Exception):
    pass


class MissingMembershipRequestPayment(Exception):
    pass


class CantBuyHonoraryMembership(Exception):
    pass
