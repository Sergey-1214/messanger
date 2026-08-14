from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MessageCreatedPayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_id: int
    author_id: UUID
    content: str
    seq: int
    created_at: datetime


class BaseEvent(BaseModel):
    event_id: UUID
    event_type: str
    occurred_at: datetime
    correlation_id: UUID

class MessageCreatedEvent(BaseEvent):
    event_type: Literal["chat.message.created"]
    message: MessageCreatedPayload
    chat_participants: list[UUID]