

from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from message_service.db.db import get_session
from message_service.dto.chat import UserChatItem
from message_service.models.models import Chat, ChatParticipant, ChatType, Message



class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat(
        self,
        users_id: set[UUID],
        chat_type: ChatType,
        is_private: bool,
        title: str | None,
    ) -> Chat:
        async with self.session.begin():
            chat = Chat(type=chat_type, is_private=is_private, title=title)
            self.session.add(chat)
            await self.session.flush()

            participants = [
                ChatParticipant(
                    chat_id=chat.id,
                    participant_id=user_id,
                )
                for user_id in users_id
            ]
            self.session.add_all(participants)

            return chat

    async def get_user_chats(self, user_id: UUID, limit: int, offset: int) -> list[UserChatItem]:
        stmt = select(Chat).join(ChatParticipant)\
                .where(ChatParticipant.participant_id == user_id)\
                .offset(offset=offset)\
                .limit(limit=limit)\
                .order_by(Chat.id)
        
        chat_result = await self.session.execute(stmt)
        chats = chat_result.scalars().all()
        chat_ids = [chat.id for chat in chats]
        private_chat_ids = [
            chat.id for chat in chats if chat.type == ChatType.PRIVATE
        ]

        private_participants: dict[int, UUID] = {}
        if private_chat_ids:
            stmt = select(ChatParticipant.participant_id, ChatParticipant.chat_id).join(Chat)\
                                .where(
                                    ChatParticipant.chat_id.in_(private_chat_ids),
                                    ChatParticipant.participant_id != user_id
                                )
        
            participant_result = await self.session.execute(stmt)
            chat_participants = participant_result.all()  

            private_participants = {
                chat_id: participant_id
                for participant_id, chat_id in chat_participants
            }

        participants_count: dict[int, int] = {}
        if chats:
            stmt = select(
                ChatParticipant.chat_id,
                func.count(ChatParticipant.participant_id),
            ).where(
                ChatParticipant.chat_id.in_([chat.id for chat in chats])
            ).group_by(ChatParticipant.chat_id)

            participants_count_result = await self.session.execute(stmt)
            participants_count = dict(participants_count_result.all())

        last_messages = await self._get_last_messages(chat_ids=chat_ids)

        return [
            UserChatItem(
                chat=chat,
                private_participant_id=private_participants.get(chat.id),
                participants_count=participants_count.get(chat.id, 0),
                last_message=last_messages.get(chat.id),
            )
            for chat in chats
        ]

    async def _get_last_messages(
        self,
        chat_ids: list[int],
    ) -> dict[int, Message]:
        if not chat_ids:
            return {}

        latest_message_seq = (
            select(
                Message.chat_id,
                func.max(Message.seq).label("seq"),
            )
            .where(
                Message.chat_id.in_(chat_ids),
                Message.is_deleted.is_(False),
            )
            .group_by(Message.chat_id)
            .subquery()
        )
        stmt = (
            select(Message)
            .join(
                latest_message_seq,
                (Message.chat_id == latest_message_seq.c.chat_id)
                & (Message.seq == latest_message_seq.c.seq),
            )
        )
        result = await self.session.execute(stmt)
        return {
            message.chat_id: message
            for message in result.scalars().all()
        }

    async def get_chat_by_id(
        self,
        chat_id: int,
    ) -> Chat | None:
        stmt = (
            select(Chat)
            .where(Chat.id == chat_id)
            .options(selectinload(Chat.chat_participants))
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_chat_for_update(self, chat_id: int) -> Chat | None:
        """Return a chat while locking it until the transaction is complete."""
        stmt = select(Chat).where(Chat.id == chat_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def chat_exists(self, chat_id: int) -> bool:
        stmt = select(Chat.id).where(Chat.id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_participant(
        self,
        chat_id: int,
        user_id: UUID,
    ) -> bool:
        stmt = select(ChatParticipant.chat_id).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.participant_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_chat_admin(
        self,
        chat_id: int,
        user_id: UUID,
    ) -> bool:
        stmt = select(ChatParticipant.chat_id).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.participant_id == user_id,
            ChatParticipant.role == "admin",
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_participant_for_update(
        self,
        chat_id: int,
        user_id: UUID,
    ) -> ChatParticipant | None:
        stmt = (
            select(ChatParticipant)
            .where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.participant_id == user_id,
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_chat_item(
        self,
        chat_id: int,
        user_id: UUID,
    ) -> UserChatItem | None:
        chat = await self.get_chat_by_id(chat_id=chat_id)
        if chat is None:
            return None

        private_participant_id = None
        if chat.type == ChatType.PRIVATE:
            for participant in chat.chat_participants:
                if participant.participant_id != user_id:
                    private_participant_id = participant.participant_id

        last_messages = await self._get_last_messages(chat_ids=[chat.id])

        return UserChatItem(
            chat=chat,
            private_participant_id=private_participant_id,
            participants_count=len(chat.chat_participants),
            last_message=last_messages.get(chat.id),
        )

    async def get_chat_participants(
        self,
        chat_id,
    ) -> list[UUID]:
        stmt = select(ChatParticipant.participant_id).join(Chat).where(Chat.id == chat_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_chat_participants(
        self,
        chat_id: int,
        user_ids: set[UUID],
    ) -> list[ChatParticipant]:
        participants = []
        for user_id in user_ids:
            participant = ChatParticipant(
                chat_id=chat_id,
                participant_id=user_id,
            )
            participants.append(participant)
        self.session.add_all(participants)
        await self.session.flush()
        return participants
        
async def get_chat_repository(
    session: AsyncSession = Depends(get_session),
) -> ChatRepository:
    return ChatRepository(session=session)

