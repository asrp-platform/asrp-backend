from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse, PermissionsResponses
from app.domains.feedback.filters import ContactMessagesFilter
from app.domains.feedback.schemas import (
    AnswerContactMessageSchema,
    ContactMessageReplyResponseSchema,
    ContactMessageResponseSchema,
)
from app.domains.feedback.use_cases import AnswerContactMessageUseCaseDep, GetContactMessagesUseCaseDep
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user


router = APIRouter(prefix="/contact-messages", tags=["Admin: Contact Messages"], dependencies=[Depends(get_admin_user)])


class GetContactMessagesResponses(InvalidRequestParamsResponses, PermissionsResponses):
    pass


@router.get(
    "",
    summary="Get contact messages",
    responses=GetContactMessagesResponses.responses,
    status_code=200,
)
async def get_contact_messages(
    permissions: AdminPermissionsDep,
    use_case: GetContactMessagesUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    order_by: str | None = Query(None, description="Sorting parameters"),
    filters: Annotated[ContactMessagesFilter, Depends()] = None,
) -> PaginatedResponse[ContactMessageResponseSchema]:
    contact_messages, messages_count = await use_case.execute(
        permissions=permissions,
        order_by=ordering or order_by,
        filters=filters.model_dump(exclude_none=True) if filters else {},
        limit=params["limit"],
        offset=params["offset"],
    )
    return PaginatedResponse(
        count=messages_count,
        data=contact_messages,
        page=params["page"],
        page_size=params["page_size"],
    )


class AnswerContactMessageResponses(PermissionsResponses):
    CONTACT_MESSAGE_NOT_FOUND = 404, "Contact message with provided id not found"


@router.post(
    "/{message_id}/answers",
    responses=AnswerContactMessageResponses.responses,
    status_code=201,
    summary="Answer a contact message",
)
async def answer_contact_message(
    message_id: int,
    body: AnswerContactMessageSchema,
    permissions: AdminPermissionsDep,
    use_case: AnswerContactMessageUseCaseDep,
) -> ContactMessageReplyResponseSchema:
    return await use_case.execute(
        message_id=message_id,
        subject=body.subject,
        answer_message=body.answer_message,
        permissions=permissions,
    )
