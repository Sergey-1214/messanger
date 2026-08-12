

from dataclasses import dataclass
from uuid import UUID

from message_service.models.models import Chat, Message


@dataclass
class UserChatItem:
    chat: Chat
    private_participant_id: UUID | None
    participants_count: int | None
    last_message: Message | None = None
