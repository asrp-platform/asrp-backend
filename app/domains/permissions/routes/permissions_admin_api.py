from fastapi import APIRouter, Depends

from app.domains.permissions.models import PermissionSchema
from app.domains.permissions.services import PermissionServiceDep
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user

router = APIRouter(prefix="/permissions", tags=["Admin: Permissions"], dependencies=[Depends(get_admin_user)])


@router.get(
    "/current-user-permissions",
    summary="List of permissions actions for the authenticated user",
)
async def get_current_user_permissions(permissions: AdminPermissionsDep) -> list[str]:
    return permissions


@router.get("", summary="List of all existing permissions")
async def get_all_permissions(
    permission_service: PermissionServiceDep,
) -> list[PermissionSchema]:
    data, count = await permission_service.get_all_permissions()
    return data
