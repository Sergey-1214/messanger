


from uuid import UUID

from fastapi import APIRouter, Depends, status

from message_service.router.chat import get_current_user_id
from message_service.schemas.message import CreateMessageRequest, MessageResponse
from message_service.service.message import MessageService, get_message_service


router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)


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


