from app.core.common.exceptions import PermissionDeniedError


def check_permissions(permission_to_check: str, permissions: list[str]) -> None:
    if permission_to_check not in permissions:
        raise PermissionDeniedError("Not enough permissions to perform this action")
