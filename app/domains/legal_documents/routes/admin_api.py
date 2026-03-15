from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.core.common.responses import PermissionsResponses
from app.domains.legal_documents.services import BylawsServiceDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep

router = APIRouter(prefix="/legal-documents", tags=["Admin: Legal Documents"])


class BylawsAdminResponses(PermissionsResponses):
    INVALID_CONTENT_TYPE = 415, "Invalid file type. Only PDF allowed."


@router.put(
    "/bylaws",
    summary="Upload or replace bylaws document",
    responses=BylawsAdminResponses.responses,
)
async def upsert_bylaws(
    service: BylawsServiceDep,
    permissions: AdminPermissionsDep,
    file: Annotated[UploadFile, File(...)],
) -> dict:
    if "legal_documents.update" not in permissions:
        raise BylawsAdminResponses.PERMISSION_ERROR

    if file.content_type != "application/pdf":
        raise BylawsAdminResponses.INVALID_CONTENT_TYPE

    path = await service.upsert(file)
    return {"url": path}


@router.delete(
    "/bylaws",
    summary="Delete bylaws document",
    status_code=204,
)
async def delete_bylaws(
    service: BylawsServiceDep,
    admin: AdminUserDep,  # noqa
    permissions: AdminPermissionsDep,
):
    if "legal_documents.delete" not in permissions:
        raise BylawsAdminResponses.PERMISSION_ERROR

    await service.delete()
