class NoMembershipError(Exception):
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


class CantChangeToHonoraryMembershipError(Exception):
    pass


class SameMembershipTypeChangeRequestError(Exception):
    pass


class InvalidMembershipTypeUpgradeError(Exception):
    pass


class InvalidMembershipTypeDowngradeError(Exception):
    pass


class MembershipAlreadySuspendedError(Exception):
    pass


class MembershipAlreadyTerminatedError(Exception):
    pass
