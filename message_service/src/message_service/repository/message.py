from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from message_service.db.db import get_session
from message_service.models.models import Message


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_message(
        self,
        chat_id: int,
        author_id: UUID,
        content: str,
        seq: int,
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            author_id=author_id,
            content=content,
            seq=seq,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_message_for_update(
        self,
        message_id: UUID,
    ) -> Message | None:
        stmt = (
            select(Message)
            .where(
                Message.id == message_id,
                Message.is_deleted.is_(False),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_message_by_id(
        self,
        message_id: UUID,
    ) -> Message | None:
        stmt = select(Message).where(
            Message.id == message_id,
            Message.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_message(self, message: Message) -> Message:
        await self.session.flush()
        await self.session.refresh(message)
        return message


async def get_message_repository(
    session: AsyncSession = Depends(get_session),
) -> MessageRepository:
    return MessageRepository(session=session)
