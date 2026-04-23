from app.core.common.exceptions import PermissionDeniedError


def check_permissions(permission_to_check, permissions) -> None:
    if permission_to_check not in permissions:
        raise PermissionDeniedError("You do not have enough permissions to perform this action")
