from unittest.mock import patch

import pytest

from app.domains.permissions.models import Permission
from app.domains.permissions.services import PermissionsService
from app.domains.users.exceptions import UserNotFoundError
from app.domains.users.models import User
from tests.fixtures.uow import PermissionsTransactionManagerBase

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="function")
def service(permissions_uow: PermissionsTransactionManagerBase) -> PermissionsService:
    return PermissionsService(permissions_uow)


async def test_set_users_permissions_success(
    service: PermissionsService,
    permissions: list[Permission],
    test_user: User,
    admin_user: User,
    insert_test_data,
):
    target_user = test_user
    actor = admin_user
    target_perms = [p.id for p in permissions[:2]]
    target_perms_objects = permissions[:2]

    with patch("app.domains.permissions.services.privileges_logger") as mock_privileges_logger:
        updated_perms = await service.set_users_permissions(target_user.id, target_perms, actor)

        assert len(updated_perms) == 2
        assert {p.id for p in updated_perms} == set(target_perms)

        mock_privileges_logger.info.assert_called_once()

        args, _ = mock_privileges_logger.info.call_args
        log_msg = args[0]
        # Format: Admin: {id} ({email}) | Target: {id} ({email}) | New Permissions: [...]
        assert f"Admin: {actor.id} ({actor.email})" in log_msg
        assert f"Target: {target_user.id} ({target_user.email})" in log_msg
        assert "New Permissions: " in log_msg
        assert "Time:" in log_msg

        expected_actions = [p.action for p in target_perms_objects]
        for action in expected_actions:
            assert action in log_msg


async def test_set_users_permissions_user_not_found(
    service: PermissionsService,
    admin_user: User,
):
    with pytest.raises(UserNotFoundError, match="User with provided ID not found"):
        await service.set_users_permissions(999999, [], admin_user)
