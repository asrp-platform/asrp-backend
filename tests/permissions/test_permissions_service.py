from unittest.mock import patch

import pytest

from app.domains.permissions.models import Permission
from app.domains.permissions.services import PermissionsService
from tests.fixtures.auth import UserFactory
from tests.fixtures.context import UserContext
from tests.fixtures.uow import PermissionsUnitOfWork

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="function")
def service(permissions_uow: PermissionsUnitOfWork) -> PermissionsService:
    return PermissionsService(permissions_uow)


async def test_set_users_permissions_success(
    service: PermissionsService,
    user_factory: UserFactory,
    admin_all_permissions_context: UserContext,
    permissions: Permission,
    insert_test_data,
):
    target_user = await user_factory(stuff=True)
    target_perms = [p.id for p in permissions[:2]]
    target_perms_objects = permissions[:2]

    with patch("app.domains.permissions.services.logger") as mock_logger:
        from datetime import datetime, timezone

        request_time_utc = datetime.now(timezone.utc).isoformat()

        updated_perms = await service.set_users_permissions(
            target_user.id, target_perms, admin_all_permissions_context.user, request_time_utc=request_time_utc
        )

        assert len(updated_perms) == 2
        assert {p.id for p in updated_perms} == set(target_perms)

        mock_logger.bind.assert_called_with(name="privileges", request_time_utc=request_time_utc)
        mock_logger.bind.return_value.info.assert_called_once()

        args, _ = mock_logger.bind.return_value.info.call_args
        log_msg = args[0]
        # Format: Admin: {id} ({email}) | Target: {id} ({email}) | New Permissions: [...]
        assert f"Admin: {admin_all_permissions_context.user.id} ({admin_all_permissions_context.user.email})" in log_msg
        assert f"Target: {target_user.id} ({target_user.email})" in log_msg
        assert "New Permissions:" in log_msg

        expected_actions = [p.action for p in target_perms_objects]
        for action in expected_actions:
            assert action in log_msg


async def test_set_users_permissions_user_not_found(
    service: PermissionsService,
    admin_all_permissions_context: UserContext,
    insert_test_data,
):
    from datetime import datetime, timezone

    request_time_utc = datetime.now(timezone.utc).isoformat()

    with pytest.raises(ValueError, match="User with provided ID not found"):
        await service.set_users_permissions(
            999999, [], admin_all_permissions_context.user, request_time_utc=request_time_utc
        )
