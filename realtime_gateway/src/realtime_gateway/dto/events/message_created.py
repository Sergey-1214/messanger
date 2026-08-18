from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from realtime_gateway.broker.rabbitmq.names import ChatRoutingKey


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

class MessageEvent(BaseEvent):
    event_type: ChatRoutingKey
    message: MessageCreatedPayload
    chat_participants: list[UUID]


class MessageCreatedEvent(MessageEvent):
    event_type: Literal["chat.message.created"]
    

class MessageUpdatedEvent(MessageEvent):
    event_type: Literal["chat.message.updated"]


class MessageDeletedEvent(MessageEvent): 
    event_type: Literal["chat.message.deleted"]