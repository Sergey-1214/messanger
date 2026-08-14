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

class MessageCreatedEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: Literal["chat.message.created"]  = (
        "chat.message.created"
    )
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    
    message: MessageCreatedPayload

    correlation_id: UUID = Field(default_factory=uuid4)