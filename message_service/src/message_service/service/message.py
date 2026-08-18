from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from message_service.broker.rabbitmq.names import ChatRoutingKey
from message_service.dto.events.message_created import MessageCreatedEvent, MessageDeletedEvent, MessagePayload, MessageUpdatedEvent
from message_service.db.db import get_session
from message_service.dto.message import MessagePage
from message_service.exception.chat import ChatNotFoundException, ForbiddenException
from message_service.exception.message import MessageNotFoundException
from message_service.models.models import Message
from message_service.repository.chat import ChatRepository, get_chat_repository
from message_service.repository.message import MessageRepository, get_message_repository
from message_service.repository.outbox import OutboxRepository, get_outbox_repository


class MessageService:
    def __init__(
        self,
        session: AsyncSession,
        chat_repo: ChatRepository,
        message_repo: MessageRepository,
        outbox_repo: OutboxRepository,
    ):
        self.session = session
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.outbox_repo = outbox_repo

    async def create_message(
        self,
        chat_id: int,
        author_id: UUID,
        content: str,
        request_id: UUID | None = None,
    ) -> Message:
        async with self.session.begin():
            chat = await self.chat_repo.get_chat_for_update(chat_id=chat_id)
            if chat is None:
                raise ChatNotFoundException()

            participant = await self.chat_repo.get_participant_for_update(
                chat_id=chat_id,
                user_id=author_id,
            )
            if participant is None:
                raise ForbiddenException(
                    detail="You are not a participant of this chat"
                )

            chat.last_message_seq += 1
            message = await self.message_repo.create_message(
                chat_id=chat_id,
                author_id=author_id,
                content=content,
                seq=chat.last_message_seq,
            )

            chat_participants = await self.chat_repo.get_chat_participants(
                chat_id=chat_id,
            )
            message_created_event = MessageCreatedEvent(
                message=MessagePayload.model_validate(message),
                chat_participants=chat_participants,
                correlation_id=request_id or uuid4(),
            )
            await self.outbox_repo.add(
                event=message_created_event,
                routing_key=ChatRoutingKey.CREATE_MESSAGE,
            )

        return message

    async def update_message_content(
        self,
        message_id: UUID,
        user_id: UUID,
        content: str,
        request_id: UUID,
    ) -> Message:
        async with self.session.begin():
            message = await self.message_repo.get_message_for_update(
                message_id=message_id,
            )
            if message is None:
                raise MessageNotFoundException()

            if message.author_id != user_id:
                raise ForbiddenException(
                    detail="You can only edit your own messages"
                )

            message.content = content
            updated_message = await self.message_repo.save_message(message)

            chat_participants = await self.chat_repo.get_chat_participants(
                chat_id=updated_message.chat_id,
            )
            message_updated_event = MessageUpdatedEvent(
                message=MessagePayload.model_validate(updated_message),
                chat_participants=chat_participants,
                correlation_id=request_id or uuid4(),
            )
            await self.outbox_repo.add(
                event=message_updated_event,
                routing_key=ChatRoutingKey.UPDATE_MESSAGE,
            )

        return updated_message

    async def get_message(
        self,
        message_id: UUID,
        user_id: UUID,
    ) -> Message:
        message = await self.message_repo.get_message_by_id(
            message_id=message_id,
        )
        if message is None:
            raise MessageNotFoundException()

        is_participant = await self.chat_repo.is_participant(
            chat_id=message.chat_id,
            user_id=user_id,
        )
        if not is_participant:
            raise ForbiddenException(
                detail="You are not a participant of this chat"
            )

        return message

    async def get_chat_messages(
        self,
        chat_id: int,
        user_id: UUID,
        limit: int,
        before_seq: int | None = None,
    ) -> MessagePage:
        is_participant = await self.chat_repo.is_participant(
            chat_id=chat_id,
            user_id=user_id,
        )
        if not is_participant:
            if not await self.chat_repo.chat_exists(chat_id=chat_id):
                raise ChatNotFoundException()
            raise ForbiddenException(
                detail="You are not a participant of this chat"
            )

        messages = await self.message_repo.get_chat_messages(
            chat_id=chat_id,
            limit=limit + 1,
            before_seq=before_seq,
        )
        has_next_page = len(messages) > limit
        page_messages = messages[:limit]
        next_cursor = (
            page_messages[-1].seq
            if has_next_page and page_messages
            else None
        )
        return MessagePage(
            messages=page_messages,
            next_cursor=next_cursor,
        )

    async def delete_message(
        self,
        message_id: UUID,
        user_id: UUID,
        request_id: UUID,
    ) -> None:
        async with self.session.begin():
            message = await self.message_repo.get_message_for_update(
                message_id=message_id,
            )
            if message is None:
                raise MessageNotFoundException()

            if message.author_id != user_id:
                raise ForbiddenException(
                    detail="You can only delete your own messages"
                )

            message.is_deleted = True
            deleted_message = await self.message_repo.save_message(message)
            
            chat_participants = await self.chat_repo.get_chat_participants(
                chat_id=deleted_message.chat_id,
            )
            message_deleted_event = MessageDeletedEvent(
                message=MessagePayload.model_validate(deleted_message),
                chat_participants=chat_participants,
                correlation_id=request_id or uuid4(),
            )
            await self.outbox_repo.add(
                event=message_deleted_event,
                routing_key=ChatRoutingKey.DELETE_MESSAGE,
            )


async def get_message_service(
    session: AsyncSession = Depends(get_session),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    outbox_repo: OutboxRepository = Depends(get_outbox_repository),
) -> MessageService:
    return MessageService(
        session=session,
        chat_repo=chat_repo,
        message_repo=message_repo,
        outbox_repo=outbox_repo,
    )
