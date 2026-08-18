from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from message_service.broker.rabbitmq.names import ChatRoutingKey


class MessagePayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_id: int
    author_id: UUID
    content: str
    seq: int
    created_at: datetime

class MessageEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: ChatRoutingKey
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    message: MessagePayload
    chat_participants: list[UUID]

    correlation_id: UUID = Field(default_factory=uuid4)


class MessageCreatedEvent(MessageEvent):
    event_type: ChatRoutingKey = ChatRoutingKey.CREATE_MESSAGE
    

class MessageUpdatedEvent(MessageEvent):
    event_type: ChatRoutingKey = ChatRoutingKey.UPDATE_MESSAGE


class MessageDeletedEvent(MessageEvent): 
    event_type: ChatRoutingKey = ChatRoutingKey.DELETE_MESSAGE
