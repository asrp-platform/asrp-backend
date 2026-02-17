from fastapi import APIRouter

from app.domains.permissions.models import PermissionSchema
from app.domains.permissions.services import PermissionServiceDep
from app.domains.shared.deps import AdminUserDep

router = APIRouter(prefix="/permissions", tags=["Admin: Permissions"])


@router.get("")
async def get_all_permissions(
    admin: AdminUserDep,  # noqa
    permission_service: PermissionServiceDep,
) -> list[PermissionSchema]:
    data, count = await permission_service.get_all_permissions()
    return [PermissionSchema.from_orm(permission) for permission in data]
