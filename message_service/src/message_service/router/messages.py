


from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from message_service.router.chat import get_current_user_id
from message_service.schemas.message import (
    CreateMessageRequest,
    MessagePageResponse,
    MessagePagination,
    MessageResponse,
    UpdateMessageRequest,
)
from message_service.service.message import MessageService, get_message_service


router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)


async def get_message_pagination(
    limit: int = Query(default=50, ge=1, le=100),
    before_seq: int | None = Query(default=None, ge=1),
) -> MessagePagination:
    return MessagePagination(limit=limit, before_seq=before_seq)


@router.post(
    "/{chat_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    chat_id: int,
    request: CreateMessageRequest,
    user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> MessageResponse:
    message = await message_service.create_message(
        chat_id=chat_id,
        author_id=user_id,
        content=request.content,
    )
    return MessageResponse.model_validate(message)


@router.get(
    "/chat/{chat_id}",
    response_model=MessagePageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_chat_messages(
    chat_id: int,
    pagination: MessagePagination = Depends(get_message_pagination),
    user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> MessagePageResponse:
    page = await message_service.get_chat_messages(
        chat_id=chat_id,
        user_id=user_id,
        limit=pagination.limit,
        before_seq=pagination.before_seq,
    )
    return MessagePageResponse(
        messages=[
            MessageResponse.model_validate(message)
            for message in page.messages
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_message(
    message_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> MessageResponse:
    message = await message_service.get_message(
        message_id=message_id,
        user_id=user_id,
    )
    return MessageResponse.model_validate(message)


@router.patch(
    "/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def update_message_content(
    message_id: UUID,
    request: UpdateMessageRequest,
    user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> MessageResponse:
    message = await message_service.update_message_content(
        message_id=message_id,
        user_id=user_id,
        content=request.content,
    )
    return MessageResponse.model_validate(message)
