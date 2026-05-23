from typing import Annotated

from fastapi import APIRouter, File, Path, UploadFile

from app.core.common.exceptions import InvalidMimeTypeError
from app.core.common.responses import PermissionsResponses
from app.core.utils.permissions import check_permissions
from app.domains.legal_documents.schemas import (
    CreateSponsorSchema,
    SponsorSchema,
    UpdateSponsorSchema,
    ViewLegalDocumentSchema,
)
from app.domains.legal_documents.services import BylawsServiceDep
from app.domains.legal_documents.use_cases.create_sponsor import CreateSponsorUseCaseDep
from app.domains.legal_documents.use_cases.delete_sponsor import DeleteSponsorUseCaseDep
from app.domains.legal_documents.use_cases.get_sponsors import GetSponsorsUseCaseDep
from app.domains.legal_documents.use_cases.update_sponsor import UpdateSponsorUseCaseDep
from app.domains.legal_documents.use_cases.upload_sponsor_logo import UploadSponsorLogoUseCaseDep
from app.domains.legal_documents.use_cases.upsert_bylaws import UpsertBylawsUseCaseDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep
from app.domains.shared.types import FileData

router = APIRouter(prefix="/legal-documents", tags=["Admin: Legal Documents"])


class BylawsAdminResponses(PermissionsResponses):
    INVALID_CONTENT_TYPE = 415, "Invalid file type. Only PDF allowed."


class CreateSponsorResponses(PermissionsResponses):
    pass


class GetAdminSponsorsResponses(PermissionsResponses):
    pass


class SponsorResponses(PermissionsResponses):
    NOT_FOUND = 404, "Sponsor with provided ID not found"


class UpdateSponsorResponses(SponsorResponses):
    pass


class DeleteSponsorResponses(SponsorResponses):
    pass


class UploadLogoResponses(PermissionsResponses):
    INVALID_CONTENT_TYPE = 415, "Invalid image content type"


@router.put(
    "/bylaws",
    summary="Upload or replace bylaws document",
    responses=BylawsAdminResponses.responses,
)
async def upsert_bylaws(
    use_case: UpsertBylawsUseCaseDep,
    permissions: AdminPermissionsDep,
    file: Annotated[UploadFile, File(...)],
) -> ViewLegalDocumentSchema:
    check_permissions("legal_documents.update", permissions)

    file_data = FileData(
        content=await file.read(),
        content_type=file.content_type,
        filename=file.filename,
    )

    try:
        url = await use_case.execute(file_data)
        return ViewLegalDocumentSchema(url=url)
    except InvalidMimeTypeError:
        raise BylawsAdminResponses.INVALID_CONTENT_TYPE


@router.delete(
    "/bylaws",
    summary="Delete bylaws document",
    status_code=204,
    responses=BylawsAdminResponses.responses,
)
async def delete_bylaws(
    service: BylawsServiceDep,
    admin: AdminUserDep,  # noqa
    permissions: AdminPermissionsDep,
):
    check_permissions("legal_documents.delete", permissions)
    await service.delete()


@router.post(
    "/sponsors",
    status_code=201,
    summary="Create a new sponsor",
    responses=CreateSponsorResponses.responses,
)
async def create_sponsor(
    data: CreateSponsorSchema,
    permissions: AdminPermissionsDep,
    use_case: CreateSponsorUseCaseDep,
) -> SponsorSchema:
    return await use_case.execute(permissions, **data.model_dump())


@router.get(
    "/sponsors",
    summary="Get list of all sponsors (Admin)",
    responses=GetAdminSponsorsResponses.responses,
)
async def get_admin_sponsors(
    use_case: GetSponsorsUseCaseDep,
    permissions: AdminPermissionsDep,
) -> list[SponsorSchema]:
    check_permissions("legal_documents.view", permissions)
    return await use_case.execute()


@router.patch(
    "/sponsors/{sponsor_id}",
    summary="Update a sponsor",
    responses=UpdateSponsorResponses.responses,
)
async def update_sponsor(
    sponsor_id: Annotated[int, Path(...)],
    data: UpdateSponsorSchema,
    permissions: AdminPermissionsDep,
    use_case: UpdateSponsorUseCaseDep,
) -> SponsorSchema:
    return await use_case.execute(permissions, sponsor_id, **data.model_dump(exclude_unset=True))


@router.delete(
    "/sponsors/{sponsor_id}",
    status_code=204,
    summary="Delete a sponsor",
    responses=DeleteSponsorResponses.responses,
)
async def delete_sponsor(
    sponsor_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: DeleteSponsorUseCaseDep,
):
    await use_case.execute(permissions, sponsor_id)


@router.put(
    "/sponsors/logos",
    summary="Upload sponsor logo",
    responses=UploadLogoResponses.responses,
)
async def upload_sponsor_logo(
    use_case: UploadSponsorLogoUseCaseDep,
    permissions: AdminPermissionsDep,
    file: Annotated[UploadFile, File(...)],
) -> ViewLegalDocumentSchema:
    check_permissions("legal_documents.update", permissions)
    file_data = FileData(
        content=await file.read(),
        content_type=file.content_type,
        filename=file.filename,
    )

    try:
        url = await use_case.execute(file_data)
        return ViewLegalDocumentSchema(url=url)
    except InvalidMimeTypeError:
        raise UploadLogoResponses.INVALID_CONTENT_TYPE
