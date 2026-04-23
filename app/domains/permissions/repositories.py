from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.permissions.models import Permission, UserPermission


class PermissionRepository(SQLAlchemyRepository):
    model = Permission


class UserPermissionRepository(SQLAlchemyRepository):
    model = UserPermission
