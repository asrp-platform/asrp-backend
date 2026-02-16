from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi_exception_responses import Responses
from pydantic import BaseModel

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse, PermissionsResponses
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.feedback.filters import ContactMessagesFilter
from app.domains.feedback.schemas import ContactMessageResponseSchema, CreateContactMessageSchema, ContactMessageReplyResponseSchema
from app.domains.feedback.services import FeedbackServiceDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep

router = APIRouter(prefix="/contact-messages", tags=["Contact Messages"])


@router.post(
    "",
    status_code=201,
)
async def create_contact_message(
    contact_message_service: FeedbackServiceDep,
    message_data: CreateContactMessageSchema,
) -> ContactMessageResponseSchema:
    contact_message = await contact_message_service.create_contact_message(message_data)
    return ContactMessageResponseSchema.from_orm(contact_message)


class GetContactMessagesResponses(InvalidRequestParamsResponses, PermissionsResponses):
    pass


@router.get("", responses=GetContactMessagesResponses.responses)
async def get_contact_messages(
    admin: AdminUserDep,  # noqa Admin auth argument
    permissions: AdminPermissionsDep,
    contact_message_service: FeedbackServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[ContactMessagesFilter, Depends()] = None,
) -> PaginatedResponse[ContactMessageResponseSchema]:
    if "feedback.view" not in permissions:
        raise GetContactMessagesResponses.PERMISSION_ERROR

    try:
        messages, messages_count = await contact_message_service.get_all_paginated_counted(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [ContactMessageResponseSchema.from_orm(message) for message in messages]
        return PaginatedResponse(
            count=messages_count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise InvalidRequestParamsResponses.INVALID_SORTER_FIELD


class AnswerContactMessageResponses(Responses):
    CONTACT_MESSAGE_NOT_FOUND = 404, "Contact message with provided id not found"


class AnswerContactMessageBody(BaseModel):
    subject: str
    answer_message: str


@router.post(
    "/{message_id}/answers",
    responses=AnswerContactMessageResponses.responses,
    status_code=201,
    summary="Creates an answer for the contact request",
)
async def answer_contact_message(
    message_id: int,
    body: AnswerContactMessageBody,
    admin: AdminUserDep,  # noqa Admin authargument
    permissions: AdminPermissionsDep,
    contact_message_service: FeedbackServiceDep,
) -> ContactMessageReplyResponseSchema:

    if 'feedback.update' not in permissions:
        raise PermissionsResponses.PERMISSION_ERROR

    try:
        reply = await contact_message_service.answer_contact_message(
            contact_message_id=message_id,
            subject=body.subject,
            answer_message=body.answer_message
        )
    except ValueError:
        raise AnswerContactMessageResponses.CONTACT_MESSAGE_NOT_FOUND

    return ContactMessageReplyResponseSchema.from_orm(reply)
