

import logging
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from message_service.clients.user_client import UserClient, get_user_client
from message_service.db.db import get_session
from message_service.exception.chat import BadRequestException, ChatNotFoundException, ForbiddenException
from message_service.models.models import Chat, ChatType
from message_service.repository.chat import ChatRepository, get_chat_repository
from message_service.schemas.chat import (
    CreateChatRequest,
    GroupChat,
    Pagination,
    PrivateChat,
    User,
    UserChats,
)
from message_service.schemas.message import MessageResponse

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        repo: ChatRepository,
        user_client: UserClient,
    ):
        self.session = session
        self.repo = repo
        self.user_client = user_client

    async def create_chat(self, user_id: UUID, request: CreateChatRequest) -> Chat:
        if user_id not in request.users_id:
            raise ForbiddenException(detail="Сannot create a chat without yourself")

        if len(request.users_id) > 10000:
            raise BadRequestException("Too much users for chat")
            
        chat = await self.repo.create_chat(
            users_id=request.users_id,
            chat_type=request.type,
            is_private=request.is_private,
            title=request.title,
        )

        return chat

    async def get_user_chats(
        self,
        user_id: UUID,
        pagination: Pagination,
    ) -> UserChats:
        chats_with_participants = await self.repo.get_user_chats(
            user_id=user_id, 
            limit=pagination.limit, 
            offset=pagination.offset,
        )

        participant_ids = {
            item.private_participant_id
            for item in chats_with_participants
            if item.private_participant_id is not None
        }
        users = await self.user_client.get_users_by_ids(participant_ids)
        users_by_id = {user.user_id: user for user in users}

        private_chats = []
        group_chats = []
        for item in chats_with_participants:
            last_message = (
                MessageResponse.model_validate(item.last_message)
                if item.last_message is not None
                else None
            )
            if item.chat.type == ChatType.GROUP:
                group_chats.append(
                    GroupChat(
                        id=item.chat.id,
                        title=item.chat.title,
                        participants_count=item.participants_count,
                        last_message=last_message,
                    )
                )
                continue

            participant_id = item.private_participant_id
            if participant_id is None or participant_id not in users_by_id:
                raise ValueError(
                    f"Participant for private chat {item.chat.id} was not found"
                )

            participant = users_by_id[participant_id]
            private_chats.append(
                PrivateChat(
                    id=item.chat.id,
                    participant=User(
                        user_id=participant.user_id,
                        username=participant.username,
                    ),
                    last_message=last_message,
                )
            )

        return UserChats(
            private_chats=private_chats,
            group_chats=group_chats,
        )

    async def get_chat_by_id(self, id: int, user_id: UUID) -> GroupChat | PrivateChat:
        chat_item = await self.repo.get_chat_item(chat_id=id, user_id=user_id)
        if chat_item is None:
            raise ChatNotFoundException("Chat not found")

        participant = await self.user_client.get_user_by_id(user_id)

        if chat_item.chat.type == ChatType.PRIVATE:
            return PrivateChat(id=id, participant=User(
                        user_id=participant.user_id,
                        username=participant.username,
                    ), last_message=chat_item.last_message)
        elif chat_item.chat.type == ChatType.GROUP:
            return GroupChat(
                id=id,
                title=chat_item.chat.title,
                participants_count=chat_item.participants_count,
                last_message=chat_item.last_message,
            )


async def get_chat_service(
    session: AsyncSession = Depends(get_session),
    repo: ChatRepository = Depends(get_chat_repository),
    user_client: UserClient = Depends(get_user_client),
):
    return AuthService(session=session, repo=repo, user_client=user_client)
