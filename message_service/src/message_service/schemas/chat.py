

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
    
