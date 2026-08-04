from dataclasses import dataclass

from message_service.models.models import Message


@dataclass(slots=True)
class MessagePage:
    messages: list[Message]
    next_cursor: int | None
