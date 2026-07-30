

from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from message_service.db.db import get_session
from message_service.dto.chat import UserChatItem
from message_service.models.models import Chat, ChatParticipant, ChatType



class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat(self, users_id: set[UUID], is_private: bool, is_group: bool
    ) -> Chat:
        async with self.session.begin():
            chat = Chat(is_private=is_private, is_group=is_group)
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
        chat_ids = [chat.id for chat in chats if chat.type == ChatType.PRIVATE]

        private_participants: dict[int, UUID] = {}
        if chat_ids:
            stmt = select(ChatParticipant.participant_id, ChatParticipant.chat_id).join(Chat)\
                                .where(
                                    ChatParticipant.chat_id.in_(chat_ids),
                                    ChatParticipant.participant_id != user_id
                                )
        
            participant_result = await self.session.execute(stmt)
            chat_participants = participant_result.all()  

            private_participants = {
                chat_id: participant_id
                for participant_id, chat_id in chat_participants
            }


        return [UserChatItem(chat=chat, private_participant_id=private_participants.get(chat.id)) for chat in chats]

    async def get_chat_by_id(self, chat_id: int) -> Chat:
        stmt = select(Chat).where(Chat.id == chat_id).options(selectinload(ChatParticipant))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

async def get_chat_repository(
    session: AsyncSession = Depends(get_session),
) -> ChatRepository:
    return ChatRepository(session=session)

