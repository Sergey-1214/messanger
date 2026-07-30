

from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from message_service.clients.user_client import UserClient, get_user_client
from message_service.db.db import get_session
from message_service.exception.chat import BadRequestException, ForbiddenException
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
            
        chat = await self.repo.create_chat(users_id=request.users_id, 
                    is_group=request.is_group, is_private=request.is_private)

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
            if item.chat.type == ChatType.GROUP:
                group_chats.append(
                    GroupChat(
                        id=item.chat.id,
                        title=item.chat.title,
                        participants_count=item.participants_count,
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
                )
            )

        return UserChats(
            private_chats=private_chats,
            group_chats=group_chats,
        )

    async def get_chat_by_id(self, id: int, user_id: UUID) -> Chat:
        chat = self.repo.get_chat_by_id(chat_id=id)
        if any(participant for participant in chat.chat_participants\
                if participant.participant_id == user_id):
            raise ForbiddenException(detail="User not in member of chat")

        return chat


async def get_chat_service(
    session: AsyncSession = Depends(get_session),
    repo: ChatRepository = Depends(get_chat_repository),
    user_client: UserClient = Depends(get_user_client),
):
    return AuthService(session=session, repo=repo, user_client=user_client)
