from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from message_service.db.db import get_session
from message_service.exception.chat import ChatNotFoundException, ForbiddenException
from message_service.models.models import Message
from message_service.repository.chat import ChatRepository, get_chat_repository
from message_service.repository.message import MessageRepository, get_message_repository


class MessageService:
    def __init__(
        self,
        session: AsyncSession,
        chat_repo: ChatRepository,
        message_repo: MessageRepository,
    ):
        self.session = session
        self.chat_repo = chat_repo
        self.message_repo = message_repo

    async def create_message(
        self,
        chat_id: int,
        author_id: UUID,
        content: str,
    ) -> Message:
        async with self.session.begin():
            chat = await self.chat_repo.get_chat_for_update(chat_id=chat_id)
            if chat is None:
                raise ChatNotFoundException()

            is_participant = await self.chat_repo.is_participant(
                chat_id=chat_id,
                user_id=author_id,
            )
            if not is_participant:
                raise ForbiddenException(
                    detail="You are not a participant of this chat"
                )

            chat.last_message_seq += 1
            return await self.message_repo.create_message(
                chat_id=chat_id,
                author_id=author_id,
                content=content,
                seq=chat.last_message_seq,
            )


async def get_message_service(
    session: AsyncSession = Depends(get_session),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> MessageService:
    return MessageService(
        session=session,
        chat_repo=chat_repo,
        message_repo=message_repo,
    )
