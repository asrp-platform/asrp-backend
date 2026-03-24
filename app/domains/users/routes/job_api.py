from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.common.exceptions import NotResourceOwnerError
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.exceptions import (
    JobNotFoundError,
    ProfessionalExperienceCurrentPositionExistsError,
    UserNotFoundError,
)
from app.domains.users.schemas import (
    JobCreateSchema,
    JobUpdateSchema,
    JobViewSchema,
)
from app.domains.users.services import JobServiceDep

router = APIRouter(
    prefix="/users/{user_id}/jobs",
    tags=["Job"],
)


class GetUserJobsResponses(Responses):
    USER_NOT_FOUND = 404, "User with proved ID not found"


@router.get(
    "",
    responses=GetUserJobsResponses.responses,
    summary="Get user jobs",
)
async def get_user_jobs(
    user_id: int,
    service: JobServiceDep,
) -> list[JobViewSchema]:
    try:
        user_jobs = await service.get_by_user_id(user_id)
        return [JobViewSchema.model_validate(job) for job in user_jobs]
    except UserNotFoundError:
        raise GetUserJobsResponses.USER_NOT_FOUND


class GetSingleUserJobResponses(GetUserJobsResponses):
    JOB_NOT_FOUND = 404, "Job with proved ID not found"


@router.get(
    "/{job_id}",
    responses=GetSingleUserJobResponses.responses,
    summary="Get user job by job ID",
)
async def get_single_user_job(
    user_id: int,
    job_id: int,
    service: JobServiceDep,
) -> JobViewSchema:
    try:
        user_job = await service.get_user_job_by_id(
            user_id=user_id,
            job_id=job_id,
        )
        return JobViewSchema.model_validate(user_job)

    except UserNotFoundError:
        raise GetSingleUserJobResponses.USER_NOT_FOUND

    except JobNotFoundError:
        raise GetSingleUserJobResponses.JOB_NOT_FOUND


class CreateUserJobResponses(GetUserJobsResponses):
    NOT_RESOURCE_OWNER = 403, "Not resource owner"
    PROFESSIONAL_EXPERIENCE_CURRENT_POSITION_EXISTS = 409, "Current position already exists in professional experience"


@router.post(
    "",
    status_code=201,
    responses=CreateUserJobResponses.responses,
    summary="Create a job for a user",
)
async def create_job_for_user(
    user_id: int,
    current_user: CurrentUserDep,
    service: JobServiceDep,
    job_creation_data: JobCreateSchema,
) -> JobViewSchema:
    try:
        user_job = await service.create_user_job(
            user_id,
            current_user.id,
            **job_creation_data.model_dump(),
        )
        return JobViewSchema.model_validate(user_job)

    except NotResourceOwnerError:
        raise CreateUserJobResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise CreateUserJobResponses.USER_NOT_FOUND

    except ProfessionalExperienceCurrentPositionExistsError:
        raise CreateUserJobResponses.PROFESSIONAL_EXPERIENCE_CURRENT_POSITION_EXISTS


class UpdateJobResponses(CreateUserJobResponses):
    pass


@router.put(
    "/{job_id}",
    responses=UpdateJobResponses.responses,
    summary="Update user job",
)
async def update_user_job(
    user_id: int,
    job_id: int,
    current_user: CurrentUserDep,
    service: JobServiceDep,
    job_update_data: JobUpdateSchema,
) -> JobViewSchema:
    try:
        user_job = await service.update_user_job(
            user_id,
            current_user.id,
            job_id,
            job_update_data.model_dump(),
        )
        return JobViewSchema.model_validate(user_job)

    except NotResourceOwnerError:
        raise UpdateJobResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise UpdateJobResponses.USER_NOT_FOUND

    except ProfessionalExperienceCurrentPositionExistsError:
        raise UpdateJobResponses.PROFESSIONAL_EXPERIENCE_CURRENT_POSITION_EXISTS


class DeleteJobResponses(
    CreateUserJobResponses,
    GetSingleUserJobResponses,
):
    pass


@router.delete(
    "/{job_id}",
    responses=DeleteJobResponses.responses,
    summary="Delete user job",
)
async def delete_user_job(
    user_id: int,
    job_id: int,
    current_user: CurrentUserDep,
    service: JobServiceDep,
) -> int:
    try:
        return await service.delete_user_job(
            user_id,
            current_user.id,
            job_id,
        )

    except NotResourceOwnerError:
        raise DeleteJobResponses.NOT_RESOURCE_OWNER

    except UserNotFoundError:
        raise DeleteJobResponses.USER_NOT_FOUND

    except JobNotFoundError:
        raise DeleteJobResponses.JOB_NOT_FOUND
