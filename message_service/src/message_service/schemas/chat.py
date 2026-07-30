

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class MessageResponse(BaseModel):
    pass 


class CreateChatRequest(BaseModel):
    users_id: set[UUID]
    is_group: bool
    is_private: bool


class User(BaseModel):
    user_id: UUID 
    username: str


class ChatResponse(BaseModel):
    users_id: set[UUID]
    is_group: bool
    is_private: bool 
    created_at: datetime


class GroupChat(BaseModel):
    type: Literal["group"] = "group"

    id: int
    title: str
    participants_count: int 
    last_message: MessageResponse


class PrivateChat(BaseModel):
    type: Literal["private"] = "private"

    id: int
    participant: User
    
    last_message: MessageResponse


class GetChatRequest(BaseModel):
    id: int


class Pagination(BaseModel):
    limit: int
    offset: int 


class Participant(BaseModel):
    user_id: UUID 
    chat_id: int


class UserChats(BaseModel):
    chats: list[GroupChat | PrivateChat]
    
