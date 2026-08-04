

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from message_service.models.models import ChatType


class CreateChatRequest(BaseModel):
    users_id: set[UUID]
    type: ChatType
    is_private: bool
    title: str | None = Field(default=None, max_length=250)

    @model_validator(mode='after')
    def check_title_group_chat(self) -> Self:
        if self.type == ChatType.PRIVATE and self.title is not None:
            raise ValueError("Private chat cannot have a title")

        if self.type == ChatType.GROUP and (
            self.title is None or not self.title.strip()
        ):
            raise ValueError("Cannot create group chat without title")

        if self.title is not None:
            self.title = self.title.strip()

        return self


class User(BaseModel):
    user_id: UUID 
    username: str


class ChatResponse(BaseModel):
    id: int
    users_id: set[UUID]
    type: ChatType
    is_private: bool 
    title: str | None
    created_at: datetime


class GroupChat(BaseModel):
    id: int
    title: str | None
    participants_count: int


class PrivateChat(BaseModel):
    id: int
    participant: User


class GetChatRequest(BaseModel):
    id: int


class Pagination(BaseModel):
    limit: int
    offset: int 


class Participant(BaseModel):
    user_id: UUID 
    chat_id: int


class UserChats(BaseModel):
    private_chats: list[PrivateChat]
    group_chats: list[GroupChat]
    
