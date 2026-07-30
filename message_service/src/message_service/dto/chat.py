

from dataclasses import dataclass
from uuid import UUID

from message_service.models.models import Chat


@dataclass
class UserChatItem:
    chat: Chat
    private_participant_id: UUID | None