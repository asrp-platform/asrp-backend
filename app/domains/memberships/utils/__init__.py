from app.domains.memberships.models import UserMembership


def has_member_access(membership: UserMembership | None) -> bool:
    return bool(membership and membership.is_active and not membership.terminated and not membership.is_suspended)
