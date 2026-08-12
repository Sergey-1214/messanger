from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from message_service.exception.chat import BadRequestException
from message_service.schemas.chat import ChatResponse, CreateChatRequest, GetChatRequest, Pagination, UserChats
from message_service.service.chat import ChatService, get_chat_service

router = APIRouter(
    prefix="/chats",
    tags=["Chats"]
)

async def get_pagination(limit: int = 10, offset: int = 0):
    if limit > 50 or offset < 0:
        raise BadRequestException(
            detail="Bad pagination params"
        )

    return Pagination(limit=limit, offset=offset)
    

async def get_current_user_id(request: Request):
    str_user_id = request.headers.get("User-Id")
    if not str_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )

    try:
        user_id = UUID(str_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad authentication credentials"
        )

    return user_id
    

@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    create_chat_request: CreateChatRequest,
    user_id: UUID = Depends(get_current_user_id),   
    user_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    chat =  await user_service.create_chat(user_id, create_chat_request)
    return ChatResponse(
        id=chat.id,
        users_id=create_chat_request.users_id,
        type=chat.type,
        is_private=chat.is_private,
        title=chat.title,
        created_at=chat.created_at,
    )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user_chats(
    pagination: Pagination = Depends(get_pagination),
    user_id: UUID = Depends(get_current_user_id),
    user_service: ChatService = Depends(get_chat_service),
) -> UserChats:
    return await user_service.get_user_chats(
        user_id=user_id, 
        pagination=pagination,
    )


@router.get("/{chat_id}")
async def get_chat_by_id(
    chat_id: int,
    user_id: UUID = Depends(get_current_user_id),
    user_service: ChatService = Depends(get_chat_service),
):
    return await user_service.get_chat_by_id(id=chat_id, user_id=user_id)
