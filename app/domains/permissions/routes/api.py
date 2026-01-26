from fastapi import APIRouter

from app.domains.permissions.models import PermissionSchema
from app.domains.shared.deps import AdminPermissionsDep

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/current-user-permissions/")
async def get_current_user_permissions(permissions: AdminPermissionsDep) -> list[PermissionSchema]:
    return [PermissionSchema.from_orm(permission) for permission in permissions]
