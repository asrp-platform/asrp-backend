from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.core.utils.permissions import check_any_permission, check_permissions
from app.domains.content.filters import CaseOfTheMonthFilter
from app.domains.content.schemas import (
    CaseOfTheMonthSchema,
    CaseTagSchema,
    CreateCaseOfTheMonthSchema,
    CreateCaseTagSchema,
    UpdateCaseOfTheMonthSchema,
    UpdateCaseTagSchema,
)
from app.domains.content.use_cases import (
    CreateCaseOfTheMonthUseCaseDep,
    CreateCaseTagUseCaseDep,
    DeleteCaseOfTheMonthUseCaseDep,
    DeleteCaseTagUseCaseDep,
    GetCaseOfTheMonthListUseCaseDep,
    GetCaseOfTheMonthUseCaseDep,
    GetCaseTagsUseCaseDep,
    GetCaseTagUseCaseDep,
    UpdateCaseOfTheMonthUseCaseDep,
    UpdateCaseTagUseCaseDep,
    UploadCaseOfTheMonthImageUseCaseDep,
)
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user
from app.domains.shared.schemas import UploadedImageSchema
from app.domains.shared.types import FileData


router = APIRouter(
    prefix="/case-of-the-month",
    tags=["Admin: Case of the Month"],
    dependencies=[Depends(get_admin_user)],
)


class CaseTagResponses(Responses):
    NOT_AUTHORIZED = 401, "Not authorized"
    PERMISSION_ERROR = 403, "Not enough permissions"
    CASE_TAG_NOT_FOUND = 404, "Case tag with provided ID not found"
    CASE_TAG_ALREADY_EXISTS = 409, "Case tag with provided name already exists"
    CASE_TAG_IN_USE = 409, "Case tag cannot be deleted because it is used by cases"


class CaseOfTheMonthResponses(Responses):
    NOT_AUTHORIZED = 401, "Not authorized"
    PERMISSION_ERROR = 403, "Not enough permissions"
    CASE_NOT_FOUND = 404, "Case of the month with provided ID not found"
    CASE_TAG_NOT_FOUND = 404, "One or more case tag IDs were not found"
    INVALID_SORTER_FIELD = 400, "Invalid sorter field"


class CaseOfTheMonthImageResponses(Responses):
    NOT_AUTHORIZED = 401, "Not authorized"
    PERMISSION_ERROR = 403, "Not enough permissions"
    FILE_TOO_LARGE = 413, "Image must be smaller than 5 MB"
    INVALID_CONTENT_TYPE = 415, "Invalid image content type"


@router.get(
    "/cases",
    summary="Get a paginated list of case of the month articles",
    status_code=200,
    responses=CaseOfTheMonthResponses.responses,
)
async def get_cases(
    use_case: GetCaseOfTheMonthListUseCaseDep,
    permissions: AdminPermissionsDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[CaseOfTheMonthFilter, Depends()] = None,
) -> PaginatedResponse[CaseOfTheMonthSchema]:
    check_permissions("case_of_the_month.view", permissions)
    data, count = await use_case.execute(
        limit=params["limit"],
        offset=params["offset"],
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True) if filters else {},
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )


@router.post(
    "/cases",
    status_code=201,
    summary="Create a case of the month article",
    responses=CaseOfTheMonthResponses.responses,
)
async def create_case(
    body: CreateCaseOfTheMonthSchema,
    permissions: AdminPermissionsDep,
    use_case: CreateCaseOfTheMonthUseCaseDep,
) -> CaseOfTheMonthSchema:
    check_permissions("case_of_the_month.create", permissions)
    return await use_case.execute(body.model_dump())


@router.post(
    "/images",
    status_code=201,
    summary="Upload an image for a case of the month article",
    responses=CaseOfTheMonthImageResponses.responses,
)
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    permissions: AdminPermissionsDep,
    use_case: UploadCaseOfTheMonthImageUseCaseDep,
) -> UploadedImageSchema:
    check_any_permission({"case_of_the_month.create", "case_of_the_month.update"}, permissions)
    file_data = FileData(
        content=await file.read(),
        content_type=file.content_type,
        filename=file.filename,
    )
    stored_file = await use_case.execute(file_data)
    return UploadedImageSchema(
        file_url=stored_file.file_url,
        object_key=stored_file.object_key,
    )


@router.get(
    "/cases/{case_id}",
    summary="Get a case of the month article by ID",
    status_code=200,
    responses=CaseOfTheMonthResponses.responses,
)
async def get_case(
    case_id: int,
    permissions: AdminPermissionsDep,
    use_case: GetCaseOfTheMonthUseCaseDep,
) -> CaseOfTheMonthSchema:
    check_permissions("case_of_the_month.view", permissions)
    return await use_case.execute(case_id)


@router.patch(
    "/cases/{case_id}",
    status_code=200,
    summary="Update a case of the month article",
    responses=CaseOfTheMonthResponses.responses,
)
async def update_case(
    case_id: int,
    body: UpdateCaseOfTheMonthSchema,
    permissions: AdminPermissionsDep,
    use_case: UpdateCaseOfTheMonthUseCaseDep,
) -> CaseOfTheMonthSchema:
    check_permissions("case_of_the_month.update", permissions)
    return await use_case.execute(case_id, body.model_dump(exclude_unset=True))


@router.delete(
    "/cases/{case_id}",
    status_code=204,
    summary="Delete a case of the month article",
    responses=CaseOfTheMonthResponses.responses,
)
async def delete_case(
    case_id: int,
    permissions: AdminPermissionsDep,
    use_case: DeleteCaseOfTheMonthUseCaseDep,
) -> None:
    check_permissions("case_of_the_month.delete", permissions)
    await use_case.execute(case_id)


@router.get(
    "/tags",
    summary="Get all case of the month tags",
    status_code=200,
    responses=CaseTagResponses.responses,
)
async def get_case_tags(permissions: AdminPermissionsDep, use_case: GetCaseTagsUseCaseDep) -> list[CaseTagSchema]:
    check_permissions("case_of_the_month.view", permissions)
    return await use_case.execute()


@router.get(
    "/tags/{tag_id}",
    summary="Get a case of the month tag by ID",
    status_code=200,
    responses=CaseTagResponses.responses,
)
async def get_case_tag(
    tag_id: int,
    permissions: AdminPermissionsDep,
    use_case: GetCaseTagUseCaseDep,
) -> CaseTagSchema:
    check_permissions("case_of_the_month.view", permissions)
    return await use_case.execute(tag_id)


@router.post(
    "/tags",
    summary="Create a case of the month tag",
    status_code=201,
    responses=CaseTagResponses.responses,
)
async def create_case_tag(
    body: CreateCaseTagSchema,
    permissions: AdminPermissionsDep,
    use_case: CreateCaseTagUseCaseDep,
) -> CaseTagSchema:
    check_permissions("case_of_the_month.create", permissions)
    return await use_case.execute(**body.model_dump())


@router.patch(
    "/tags/{tag_id}",
    summary="Update a case of the month tag",
    status_code=200,
    responses=CaseTagResponses.responses,
)
async def update_case_tag(
    tag_id: int,
    body: UpdateCaseTagSchema,
    permissions: AdminPermissionsDep,
    use_case: UpdateCaseTagUseCaseDep,
) -> CaseTagSchema:
    check_permissions("case_of_the_month.update", permissions)
    return await use_case.execute(tag_id, body.model_dump(exclude_unset=True))


@router.delete(
    "/tags/{tag_id}",
    summary="Delete a case of the month tag",
    status_code=204,
    responses=CaseTagResponses.responses,
)
async def delete_case_tag(
    tag_id: int,
    permissions: AdminPermissionsDep,
    use_case: DeleteCaseTagUseCaseDep,
) -> None:
    check_permissions("case_of_the_month.delete", permissions)
    await use_case.execute(tag_id)
